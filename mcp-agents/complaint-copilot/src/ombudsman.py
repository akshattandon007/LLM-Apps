"""Ombudsman and regulator finder — maps companies and issue types to the right body."""

from __future__ import annotations

from src.models import Country, IssueType, OmbudsmanInfo

# ---------------------------------------------------------------------------
# Simulated ombudsman database
#
# In a real deployment this would query a live API or a more comprehensive
# database. For v0.1 we cover the most common UK, US, and EU bodies.
#
# Matching strategy:
#   1. Keyword match on company name (e.g. "British Airways" -> CAA)
#   2. Fall back to issue-type-based general ombudsman
# ---------------------------------------------------------------------------

# ── Known company → specific ombudsman overrides ─────────────────────
_COMPANY_OVERRIDES: dict[str, OmbudsmanInfo] = {
    # Airlines — US
    "delta": OmbudsmanInfo(
        name="US Department of Transportation — Aviation Consumer Protection",
        url="https://www.transportation.gov/airconsumer",
        jurisdiction="All US and foreign airlines operating to/from the US",
        eligibility="Any passenger on a flight to/from or within the US",
        notes="File a complaint via aviationconsumer.dot.gov. DOT investigates but does not award compensation directly.",
    ),
    "united": OmbudsmanInfo(
        name="US Department of Transportation — Aviation Consumer Protection",
        url="https://www.transportation.gov/airconsumer",
        jurisdiction="All US and foreign airlines operating to/from the US",
        eligibility="Any passenger on a flight to/from or within the US",
    ),
    "american airlines": OmbudsmanInfo(
        name="US Department of Transportation — Aviation Consumer Protection",
        url="https://www.transportation.gov/airconsumer",
        jurisdiction="All US and foreign airlines operating to/from the US",
        eligibility="Any passenger on a flight to/from or within the US",
    ),
    "southwest": OmbudsmanInfo(
        name="US Department of Transportation — Aviation Consumer Protection",
        url="https://www.transportation.gov/airconsumer",
        jurisdiction="All US and foreign airlines operating to/from the US",
        eligibility="Any passenger on a flight to/from or within the US",
    ),
    # Airlines — UK / EU
    "british airways": OmbudsmanInfo(
        name="UK Civil Aviation Authority (CAA)",
        url="https://www.caa.co.uk/passengers",
        jurisdiction="UK airlines and flights departing from UK airports",
        eligibility="Any passenger on a flight operated by a UK carrier or departing from a UK airport",
        notes="CAA handles complaints about denied boarding, delays, cancellations. They offer an ADR scheme.",
    ),
    "ryanair": OmbudsmanInfo(
        name="Irish Aviation Authority / CAA (for UK departures)",
        url="https://www.caa.co.uk/passengers",
        jurisdiction="Flights departing from UK airports",
        eligibility="Passengers on flights departing from UK airports",
    ),
    "easyjet": OmbudsmanInfo(
        name="UK Civil Aviation Authority (CAA)",
        url="https://www.caa.co.uk/passengers",
        jurisdiction="UK airlines and flights departing from UK airports",
        eligibility="Any passenger on flights to/from the UK operated by easyJet",
    ),
    "emirates": OmbudsmanInfo(
        name="UK Civil Aviation Authority (CAA) — for UK departures",
        url="https://www.caa.co.uk/passengers",
        jurisdiction="Flights departing from UK airports",
        eligibility="Any passenger whose flight departed from a UK airport",
    ),
    # UK banks / financial services
    "barclays": OmbudsmanInfo(
        name="Financial Ombudsman Service (FOS)",
        url="https://www.financial-ombudsman.org.uk",
        jurisdiction="UK-regulated financial services",
        eligibility="Individual consumers and small businesses with annual turnover under £6.5m",
        notes="Must complain to the bank first and give them 8 weeks to respond. FOS is free for consumers.",
    ),
    "hsbc": OmbudsmanInfo(
        name="Financial Ombudsman Service (FOS)",
        url="https://www.financial-ombudsman.org.uk",
        jurisdiction="UK-regulated financial services",
        eligibility="Individual consumers and small businesses with annual turnover under £6.5m",
    ),
    "lloyds": OmbudsmanInfo(
        name="Financial Ombudsman Service (FOS)",
        url="https://www.financial-ombudsman.org.uk",
        jurisdiction="UK-regulated financial services",
        eligibility="Individual consumers and small businesses with annual turnover under £6.5m",
    ),
    "natwest": OmbudsmanInfo(
        name="Financial Ombudsman Service (FOS)",
        url="https://www.financial-ombudsman.org.uk",
        jurisdiction="UK-regulated financial services",
        eligibility="Individual consumers and small businesses with annual turnover under £6.5m",
    ),
    # US banks / financial services
    "chase": OmbudsmanInfo(
        name="Consumer Financial Protection Bureau (CFPB)",
        url="https://www.consumerfinance.gov/complaint/",
        jurisdiction="US consumer financial products and services",
        eligibility="Any US consumer with a complaint about a financial product or service",
        notes="File a complaint at cfpb.gov/complaint. CFPB sends to company and facilitates response.",
    ),
    "bank of america": OmbudsmanInfo(
        name="Consumer Financial Protection Bureau (CFPB)",
        url="https://www.consumerfinance.gov/complaint/",
        jurisdiction="US consumer financial products and services",
        eligibility="Any US consumer with a complaint about a financial product or service",
    ),
    "wells fargo": OmbudsmanInfo(
        name="Consumer Financial Protection Bureau (CFPB)",
        url="https://www.consumerfinance.gov/complaint/",
        jurisdiction="US consumer financial products and services",
        eligibility="Any US consumer with a complaint about a financial product or service",
    ),
    # Telecoms — UK
    "bt": OmbudsmanInfo(
        name="Communications Ombudsman (Ombudsman Services: Communications)",
        url="https://www.ombudsman-services.org/sectors/communications",
        jurisdiction="UK telecom and broadband providers",
        eligibility="Residential consumers and small businesses (fewer than 10 employees)",
        notes="Must complain to the provider first and give 8 weeks. Ombudsman Services is free for consumers.",
    ),
    "sky": OmbudsmanInfo(
        name="Communications Ombudsman (Ombudsman Services: Communications)",
        url="https://www.ombudsman-services.org/sectors/communications",
        jurisdiction="UK telecom and broadband providers",
        eligibility="Residential consumers and small businesses (fewer than 10 employees)",
    ),
    "virgin media": OmbudsmanInfo(
        name="Communications Ombudsman (Ombudsman Services: Communications)",
        url="https://www.ombudsman-services.org/sectors/communications",
        jurisdiction="UK telecom and broadband providers",
        eligibility="Residential consumers and small businesses (fewer than 10 employees)",
    ),
    # Energy — UK
    "british gas": OmbudsmanInfo(
        name="Energy Ombudsman (Ombudsman Services: Energy)",
        url="https://www.ombudsman-services.org/sectors/energy",
        jurisdiction="UK energy suppliers and networks",
        eligibility="Domestic energy consumers and small businesses",
        notes="Must complain to the supplier first and give 8 weeks.",
    ),
    "eon": OmbudsmanInfo(
        name="Energy Ombudsman (Ombudsman Services: Energy)",
        url="https://www.ombudsman-services.org/sectors/energy",
        jurisdiction="UK energy suppliers and networks",
        eligibility="Domestic energy consumers and small businesses",
    ),
    "edf": OmbudsmanInfo(
        name="Energy Ombudsman (Ombudsman Services: Energy)",
        url="https://www.ombudsman-services.org/sectors/energy",
        jurisdiction="UK energy suppliers and networks",
        eligibility="Domestic energy consumers and small businesses",
    ),
}

# ── Fallback by issue type ────────────────────────────────────────────
_ISSUE_FALLBACKS: dict[IssueType, list[OmbudsmanInfo]] = {
    IssueType.DELAYED_CANCELLED_FLIGHT: [
        OmbudsmanInfo(
            name="US Department of Transportation — Aviation Consumer Protection",
            url="https://www.transportation.gov/airconsumer",
            jurisdiction="All US and foreign airlines",
            eligibility="Any passenger",
        ),
        OmbudsmanInfo(
            name="UK Civil Aviation Authority (CAA)",
            url="https://www.caa.co.uk/passengers",
            jurisdiction="UK airlines and flights departing from UK airports",
            eligibility="Any passenger on flights with UK connection",
        ),
        OmbudsmanInfo(
            name="European Consumer Centre Network (ECC-Net) — Travel",
            url="https://ec.europa.eu/consumers/odr",
            jurisdiction="EU airlines and flights within EU",
            eligibility="EU residents on intra-EU flights",
        ),
    ],
    IssueType.DEFECTIVE_PRODUCT: [
        OmbudsmanInfo(
            name="Federal Trade Commission (FTC) — Report Fraud",
            url="https://reportfraud.ftc.gov",
            jurisdiction="US interstate commerce",
            eligibility="Any US consumer",
            notes="FTC collects complaints but does not resolve individual cases.",
        ),
        OmbudsmanInfo(
            name="US Consumer Product Safety Commission (CPSC)",
            url="https://www.saferproducts.gov",
            jurisdiction="US consumer product safety",
            eligibility="Anyone reporting a product safety defect",
        ),
        OmbudsmanInfo(
            name="Citizens Advice Consumer Service (UK)",
            url="https://www.citizensadvice.org.uk/consumer/",
            jurisdiction="England and Wales",
            eligibility="Any UK consumer",
        ),
        OmbudsmanInfo(
            name="European Consumer Centre Network (ECC-Net)",
            url="https://www.eccnet.eu",
            jurisdiction="EU cross-border consumer issues",
            eligibility="EU residents with cross-border complaints",
        ),
    ],
    IssueType.OVERCHARGE_BILLING_ERROR: [
        OmbudsmanInfo(
            name="Consumer Financial Protection Bureau (CFPB)",
            url="https://www.consumerfinance.gov/complaint/",
            jurisdiction="US consumer financial products",
            eligibility="Any US consumer",
        ),
        OmbudsmanInfo(
            name="Financial Ombudsman Service (UK)",
            url="https://www.financial-ombudsman.org.uk",
            jurisdiction="UK-regulated financial services",
            eligibility="Individual consumers and small businesses",
        ),
        OmbudsmanInfo(
            name="European Consumer Centre Network (ECC-Net)",
            url="https://www.eccnet.eu",
            jurisdiction="EU cross-border consumer issues",
            eligibility="EU residents with cross-border complaints",
        ),
    ],
    IssueType.POOR_SERVICE: [
        OmbudsmanInfo(
            name="Federal Trade Commission (FTC) — Report Fraud",
            url="https://reportfraud.ftc.gov",
            jurisdiction="US interstate commerce",
            eligibility="Any US consumer",
        ),
        OmbudsmanInfo(
            name="Citizens Advice Consumer Service (UK)",
            url="https://www.citizensadvice.org.uk/consumer/",
            jurisdiction="England and Wales",
            eligibility="Any UK consumer",
        ),
        OmbudsmanInfo(
            name="European Consumer Centre Network (ECC-Net)",
            url="https://www.eccnet.eu",
            jurisdiction="EU cross-border consumer issues",
            eligibility="EU residents with cross-border complaints",
        ),
    ],
    IssueType.LANDLORD_TENANT: [
        OmbudsmanInfo(
            name="US Department of Housing and Urban Development (HUD)",
            url="https://www.hud.gov/topics/rental_assistance/tenantrights",
            jurisdiction="US federally-assisted housing",
            eligibility="Tenants in federally-assisted housing",
            notes="For private rentals, contact your state Attorney General or local housing authority.",
        ),
        OmbudsmanInfo(
            name="The Property Ombudsman (UK)",
            url="https://www.tpos.co.uk",
            jurisdiction="UK estate agents and letting agents",
            eligibility="Landlords, tenants, and buyers dealing with TPO-member agents",
        ),
        OmbudsmanInfo(
            name="Shelter (UK)",
            url="https://england.shelter.org.uk/get_help",
            jurisdiction="England — housing advice",
            eligibility="Anyone needing housing advice",
            notes="Shelter provides free advice on landlord-tenant issues, eviction, and disrepair.",
        ),
    ],
    IssueType.WARRANTY_CLAIM: [
        OmbudsmanInfo(
            name="Federal Trade Commission (FTC) — Warranty Issues",
            url="https://reportfraud.ftc.gov",
            jurisdiction="US interstate commerce",
            eligibility="Any US consumer",
        ),
        OmbudsmanInfo(
            name="Citizens Advice Consumer Service (UK)",
            url="https://www.citizensadvice.org.uk/consumer/",
            jurisdiction="England and Wales",
            eligibility="Any UK consumer",
        ),
        OmbudsmanInfo(
            name="European Consumer Centre Network (ECC-Net)",
            url="https://www.eccnet.eu",
            jurisdiction="EU cross-border consumer issues",
            eligibility="EU residents with cross-border complaints",
        ),
    ],
    IssueType.CONTRACT_DISPUTE: [
        OmbudsmanInfo(
            name="Federal Trade Commission (FTC) — Report Fraud",
            url="https://reportfraud.ftc.gov",
            jurisdiction="US interstate commerce",
            eligibility="Any US consumer",
        ),
        OmbudsmanInfo(
            name="Citizens Advice Consumer Service (UK)",
            url="https://www.citizensadvice.org.uk/consumer/",
            jurisdiction="England and Wales",
            eligibility="Any UK consumer",
        ),
        OmbudsmanInfo(
            name="European Consumer Centre Network (ECC-Net)",
            url="https://www.eccnet.eu",
            jurisdiction="EU cross-border consumer issues",
            eligibility="EU residents with cross-border complaints",
        ),
    ],
}

# ── General fallback — for unknown companies ─────────────────────────
_GENERAL_FALLBACK: list[OmbudsmanInfo] = [
    OmbudsmanInfo(
        name="Federal Trade Commission (FTC) — Report Fraud",
        url="https://reportfraud.ftc.gov",
        jurisdiction="US interstate commerce",
        eligibility="Any US consumer",
    ),
    OmbudsmanInfo(
        name="Citizens Advice Consumer Service (UK)",
        url="https://www.citizensadvice.org.uk/consumer/",
        jurisdiction="England and Wales",
        eligibility="Any UK consumer",
    ),
    OmbudsmanInfo(
        name="European Consumer Centre Network (ECC-Net)",
        url="https://www.eccnet.eu",
        jurisdiction="EU cross-border consumer issues",
        eligibility="EU residents with cross-border complaints",
    ),
]


def find_ombudsman(company: str, issue_type: IssueType) -> list[OmbudsmanInfo]:
    """Find the right ombudsman or regulator for a company and issue type.

    Strategy:
      1. Try to match the company name against known overrides (case-insensitive).
      2. If no override, use issue-type-based fallback.
      3. If no issue fallback, return the general fallback list.
    """
    company_lower = company.strip().lower()

    override = _COMPANY_OVERRIDES.get(company_lower)
    if override is not None:
        return [override]

    fallback = _ISSUE_FALLBACKS.get(issue_type)
    if fallback is not None:
        return fallback

    return _GENERAL_FALLBACK
