"""Complaint Copilot MCP Server.

Exposes 5 tools via the MCP protocol:
  1. draft_complaint     — Generate a formal complaint letter
  2. find_ombudsman      — Find the right ombudsman/regulator
  3. statutory_rights    — Look up consumer rights by issue type + country
  4. track_complaint     — Track complaint status and escalation
  5. escalate_to_regulator — Generate a formal regulatory referral letter
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `import src` works
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from mcp.server.fastmcp import FastMCP

from src.models import Country, IssueType
from src.drafter import draft_complaint as _draft
from src.ombudsman import find_ombudsman as _find_ombudsman
from src.rights import get_rights
from src.tracker import track_complaint as _track
from src.escalation import escalate_to_regulator as _escalate

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP("Complaint Copilot")


def _resolve_issue_type(raw: str | None) -> IssueType | None:
    """Convert a raw string to an IssueType enum, or None."""
    if raw is None:
        return None
    raw_clean = raw.strip().lower().replace(" ", "_").replace("-", "_")
    for member in IssueType:
        if member.value == raw_clean:
            return member
    return None


def _resolve_country(raw: str | None) -> Country | None:
    """Convert a raw string to a Country enum, or None."""
    if raw is None:
        return None
    raw_clean = raw.strip().lower()
    for member in Country:
        if member.value == raw_clean:
            return member
    return None


def _format_ombudsman_list(company: str, issue_type: IssueType) -> str:
    """Format ombudsman results as readable text."""
    results = _find_ombudsman(company, issue_type)
    lines = [
        f"Ombudsmen / Regulators for: {company}",
        f"Issue type: {issue_type.value.replace('_', ' ').title()}",
        "",
    ]
    for i, info in enumerate(results, 1):
        lines.append(f"{i}. {info.name}")
        lines.append(f"   URL: {info.url}")
        lines.append(f"   Jurisdiction: {info.jurisdiction}")
        lines.append(f"   Eligibility: {info.eligibility}")
        if info.notes:
            lines.append(f"   Notes: {info.notes}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def draft_complaint(
    company: str,
    issue: str,
    amount: str | None = None,
    outcome: str | None = None,
    issue_type: str | None = None,
    country: str | None = None,
) -> str:
    """Generate a formal complaint letter addressed to a company.

    Args:
        company: Name of the company or entity being complained about.
        issue: Description of what went wrong.
        amount: Optional amount claimed (e.g. '$350' or 'repair cost').
        outcome: Optional desired resolution.
        issue_type: Optional issue type keyword (delayed_cancelled_flight,
            defective_product, overcharge_billing_error, poor_service,
            landlord_tenant, warranty_claim, contract_dispute).
        country: Optional country code (us, uk, eu) for legal references.

    Returns:
        A complete formal complaint letter as a string.
    """
    it = _resolve_issue_type(issue_type)
    ct = _resolve_country(country)
    return _draft(
        company=company,
        issue=issue,
        amount=amount,
        outcome=outcome,
        issue_type=it,
        country=ct,
    )


@mcp.tool()
def find_ombudsman(company: str, issue_type: str) -> str:
    """Find the appropriate ombudsman or regulator for a company and issue type.

    Args:
        company: Name of the company.
        issue_type: Type of issue (delayed_cancelled_flight, defective_product,
            overcharge_billing_error, poor_service, landlord_tenant,
            warranty_claim, contract_dispute).

    Returns:
        Formatted list of ombudsmen/regulators with URLs and eligibility info.
    """
    it = _resolve_issue_type(issue_type)
    if it is None:
        supported = ", ".join(m.value for m in IssueType)
        return (
            f"Unknown issue type: '{issue_type}'.\n"
            f"Supported types: {supported}"
        )
    return _format_ombudsman_list(company, it)


@mcp.tool()
def statutory_rights(issue_type: str, country: str) -> str:
    """Look up consumer statutory rights for a specific issue type and country.

    Args:
        issue_type: Type of issue (delayed_cancelled_flight, defective_product,
            overcharge_billing_error, poor_service, landlord_tenant,
            warranty_claim, contract_dispute).
        country: Country code (us, uk, eu).

    Returns:
        Consumer rights information including legal references and deadlines.
    """
    it = _resolve_issue_type(issue_type)
    ct = _resolve_country(country)

    if it is None:
        supported = ", ".join(m.value for m in IssueType)
        return (
            f"Unknown issue type: '{issue_type}'.\n"
            f"Supported types: {supported}"
        )
    if ct is None:
        supported = ", ".join(m.value for m in Country)
        return (
            f"Unknown country: '{country}'.\n"
            f"Supported countries: {supported}"
        )

    right = get_rights(it, ct)
    if right is None:
        return (
            f"No rights information available for "
            f"'{issue_type}' in '{country.upper()}'."
        )

    return f"""\
Statutory Rights — {it.value.replace('_', ' ').title()} ({country.upper()})

Right: {right.right}

Summary:
{right.summary}

Deadline: {right.deadline}

Legal Reference: {right.reference}

Details:
{right.details}
"""


@mcp.tool()
def track_complaint(company: str, reference: str | None = None) -> str:
    """Track the status of a complaint or get a tracking template.

    Args:
        company: Name of the company being complained about.
        reference: Optional complaint reference number to look up.

    Returns:
        Current status or tracking template with next steps.
    """
    return _track(company=company, reference=reference)


@mcp.tool()
def escalate_to_regulator(company: str, ombudsman: str, case_summary: str) -> str:
    """Generate a formal referral letter to escalate a complaint to a regulator.

    Args:
        company: Name of the company.
        ombudsman: Name of the ombudsman or regulator.
        case_summary: Summary of the case and why escalation is needed.

    Returns:
        A formal referral letter as a string.
    """
    # Try to find matching ombudsman info for reference details
    results = _find_ombudsman(company, IssueType.CONTRACT_DISPUTE)
    info = next((r for r in results if ombudsman.lower() in r.name.lower()), None)

    return _escalate(
        company=company,
        ombudsman=ombudsman,
        case_summary=case_summary,
        ombudsman_info=info,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server via stdio transport (for MCP hosts)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
