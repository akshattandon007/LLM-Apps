"""License, insurance, and bond verification for home service professionals.

This module simulates checking state-level licensing databases.
In production, this would call APIs from:
  - State Contractor License Boards (CSLB in CA, etc.)
  - NASCLA (National Association of State Contractors Licensing Agencies)
  - Insurance verification via AM Best or similar

The mock returns verified/stale/not_found statuses to exercise all code paths.
"""

import random
from datetime import date, timedelta

from src.service_db import get_pro_by_name


# License data sources — simulated → real integration would hit:
#   - https://www.cslb.ca.gov/ (California Contractors State License Board)
#   - https://www.nascla.org/ (National association)
#   - State-specific DOI for insurance verification

LICENSE_STATUSES = ["active", "active", "active", "expired", "suspended"]
INSURANCE_STATUSES = ["valid", "valid", "valid", "lapsed", "not_found"]
BOND_STATUSES = ["bonded", "bonded", "bonded", "not_bonded"]

STATE_LICENSING_BOARDS = {
    "NY": "New York Department of Consumer Affairs — Home Improvement Contractor License",
    "CA": "California Contractors State License Board (CSLB)",
    "TX": "Texas Department of Licensing and Regulation (TDLR)",
    "FL": "Florida Department of Business and Professional Regulation (DBPR)",
    "IL": "Illinois Department of Financial & Professional Regulation (IDFPR)",
}


def check_license(company: str, state: str) -> dict:
    """Check license/insurance/bond status for a company in a given state.

    Returns a dict with status details, verification source, and a human-readable summary.
    """
    pro = get_pro_by_name(company)
    if pro is None:
        # Still return a mock result even for unknown companies
        return _simulate_check(company, state)

    return _simulate_check(pro.company if pro.company != company else company, state, known_pro=pro)


def _simulate_check(company: str, state: str, known_pro=None) -> dict:
    """Simulate a licensing database check.

    Uses the pro's real data if available, otherwise generates plausible mock data.
    """
    # Determine the state licensing board
    board = STATE_LICENSING_BOARDS.get(state.upper(), f"{state.upper()} Contractor Licensing Board")

    if known_pro:
        # Use actual known data as base
        license_status = "active" if known_pro.licensed else "not_found"
        insurance_status = "valid" if known_pro.insured else "lapsed"
        bond_status = "bonded" if known_pro.bonded else "not_bonded"

        # Occasionally randomize to make it interesting
        if known_pro.licensed and random.random() < 0.1:
            license_status = random.choice(["expired", "suspended"])
        if known_pro.insured and random.random() < 0.1:
            insurance_status = "lapsed"
    else:
        license_status = random.choice(LICENSE_STATUSES)
        insurance_status = random.choice(INSURANCE_STATUSES)
        bond_status = random.choice(BOND_STATUSES)

    expiry = date.today() + timedelta(days=random.randint(-200, 365))

    license_number = f"{state.upper()}-{random.randint(100000, 999999)}"

    summary_parts = []
    if license_status == "active":
        summary_parts.append(f"✅ License **active** (No. {license_number}, expires {expiry.isoformat()})")
    elif license_status == "expired":
        summary_parts.append(f"⚠️ License **expired** (No. {license_number}, expired {expiry.isoformat()})")
    elif license_status == "suspended":
        summary_parts.append(f"❌ License **suspended** (No. {license_number})")
    else:
        summary_parts.append(f"❌ License **not found** in {board}")

    if insurance_status == "valid":
        summary_parts.append("✅ General liability insurance **valid**")
    elif insurance_status == "lapsed":
        summary_parts.append("⚠️ Insurance **lapsed**")
    else:
        summary_parts.append("❌ Insurance coverage **not found**")

    if bond_status == "bonded":
        summary_parts.append("✅ Surety bond **active**")
    else:
        summary_parts.append("❌ No surety bond on file")

    return {
        "company": company,
        "state": state.upper(),
        "license_number": license_number,
        "license_status": license_status,
        "insurance_status": insurance_status,
        "bond_status": bond_status,
        "expiration_date": expiry.isoformat(),
        "verification_source": board,
        "summary": "\n".join(summary_parts),
    }