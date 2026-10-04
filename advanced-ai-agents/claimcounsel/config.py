"""
Configuration for ClaimCounsel — multi-agent insurance claims assistant.
"""

import os

# LLM configuration — uses OpenAI-compatible endpoint
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.3"))

# Paths
CLAIMS_DIR = os.environ.get("CLAIMCOUNSEL_CLAIMS_DIR", os.path.expanduser("~/claimcounsel_data/claims"))
OUTPUT_DIR = os.environ.get("CLAIMCOUNSEL_OUTPUT_DIR", os.path.expanduser("~/claimcounsel_data/output"))
POLICIES_DIR = os.environ.get("CLAIMCOUNSEL_POLICIES_DIR", os.path.expanduser("~/claimcounsel_data/policies"))
DOCUMENTS_DIR = os.environ.get("CLAIMCOUNSEL_DOCUMENTS_DIR", os.path.expanduser("~/claimcounsel_data/documents"))

# US State insurance claim deadlines (days to file)
CLAIM_DEADLINES = {
    "AL": 730, "AK": 365, "AZ": 730, "AR": 365, "CA": 365,
    "CO": 365, "CT": 365, "DE": 365, "FL": 365, "GA": 365,
    "HI": 730, "ID": 365, "IL": 365, "IN": 365, "IA": 365,
    "KS": 365, "KY": 365, "LA": 365, "ME": 365, "MD": 365,
    "MA": 365, "MI": 365, "MN": 365, "MS": 365, "MO": 365,
    "MT": 730, "NE": 365, "NV": 365, "NH": 365, "NJ": 365,
    "NM": 365, "NY": 365, "NC": 365, "ND": 365, "OH": 365,
    "OK": 365, "OR": 365, "PA": 365, "RI": 365, "SC": 365,
    "SD": 365, "TN": 365, "TX": 365, "UT": 365, "VT": 730,
    "VA": 365, "WA": 365, "WV": 365, "WI": 365, "WY": 365,
}

# Claim types and typical required documents
CLAIM_TYPE_DOCUMENTS = {
    "auto": [
        "Police report", "Photos of damage", "Driver's license",
        "Vehicle registration", "Insurance ID card", "Witness contact info",
    ],
    "home": [
        "Photos of damage", "Police report (if theft/burglary)",
        "Inventory of damaged items", "Receipts for damaged items",
        "Contractor estimates", "Proof of loss form",
    ],
    "health": [
        "Medical records", "Itemized bills", "Doctor's statement",
        "Prescription receipts", "Explanation of Benefits (EOB)",
        "Referral/authorization forms",
    ],
    "life": [
        "Certified death certificate", "Policy document",
        "Claimant's statement", "Proof of identity",
        "Physician's statement (if within contestability period)",
    ],
    "travel": [
        "Trip itinerary", "Receipts for cancelled bookings",
        "Medical reports (if injury claim)", "Police report (if theft)",
        "Airline/hotel cancellation confirmation",
    ],
}