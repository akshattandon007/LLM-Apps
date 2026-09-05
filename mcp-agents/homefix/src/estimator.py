"""Fair price estimation by service type, description keywords, and region."""

import math
import re

from src.service_db import (
    SERVICE_DEFINITIONS,
    BASELINE_PRICES,
    REGIONAL_PRICING,
    DEFAULT_REGIONAL_MULTIPLIER,
    URGENCY_SURCHARGE,
)


# Complexity keywords that bump prices
_COMPLEXITY_UPSELL = {
    "emergency": 0.50,   # after-hours / holiday
    "urgent": 0.35,
    "after.hours": 0.40,
    "weekend": 0.30,
    "holiday": 0.50,
    "major": 0.30,
    "full": 0.20,
    "replace": 0.25,
    "install": 0.20,
    "rewire": 0.40,
    "reroute": 0.35,
    "excavate": 0.60,
    "structural": 0.50,
    "permit": 0.15,
    "code.upgrade": 0.25,
    "custom": 0.25,
}

# Discount keywords — simpler scope
_COMPLEXITY_DOWNSELL = {
    "simple": -0.20,
    "quick": -0.15,
    "minor": -0.20,
    "diagnostic": -0.25,
    "inspection": -0.15,
    "estimate": -0.30,
}


def extract_zip_state(zip_code: str) -> str:
    """Extract a rough state code from ZIP prefix.
    This is a simplified mapping for demo purposes.
    Full implementation would use a ZIP→state database.
    """
    prefix = int(zip_code[:3]) if zip_code[:3].isdigit() else 0

    # Simplified 3-digit prefix → state mapping
    if 100 <= prefix <= 149:
        return "NY"
    elif 900 <= prefix <= 966:
        return "CA"
    elif 733 <= prefix <= 799:
        return "TX"
    elif 320 <= prefix <= 349:
        return "FL"
    elif 600 <= prefix <= 629:
        return "IL"
    else:
        return "NY"  # Default to NY as common baseline


def infer_complexity_factor(description: str) -> float:
    """Parse the job description for complexity keywords and return a multiplier."""
    desc = description.lower()
    factor = 0.0

    for keyword, bump in _COMPLEXITY_UPSELL.items():
        pattern = keyword.replace(".", r"[\s\-.]")
        if re.search(pattern, desc):
            factor += bump

    for keyword, discount in _COMPLEXITY_DOWNSELL.items():
        pattern = keyword.replace(".", r"[\s\-.]")
        if re.search(pattern, desc):
            factor += discount

    # Emergency keyword triggers urgency surcharge
    if re.search(r"\b(emergency|urgent|24\/?7|after.?hours)\b", desc):
        factor += URGENCY_SURCHARGE

    # Cap at reasonable bounds
    return max(-0.30, min(1.50, factor))


def get_estimate(service: str, description: str, zip_code: str) -> str:
    """Generate a fair price range estimate based on regional market data.

    Factors considered:
    - Baseline price range for the service type
    - Regional cost multiplier (NYC vs rural TX)
    - Complexity keywords in the description
    - Urgency/emergency surcharge
    """
    service_key = service.lower().replace(" ", "_")

    # Validate service type
    baseline = BASELINE_PRICES.get(service_key)
    if baseline is None:
        # Try matching to known service types
        for st, defn in SERVICE_DEFINITIONS.items():
            if service_key == st.value:
                baseline = BASELINE_PRICES.get(st.value)
                break
    if baseline is None:
        return f"Unable to estimate: unknown service type '{service}'"

    # Regional multiplier
    state = extract_zip_state(zip_code)
    regional_data = REGIONAL_PRICING.get(state, {})
    multiplier = regional_data.get(service_key, DEFAULT_REGIONAL_MULTIPLIER)

    # Complexity factor from description
    complexity = infer_complexity_factor(description)

    low, high = baseline
    base_mid = (low + high) / 2

    # Apply adjustments
    adjusted_low = low * multiplier
    adjusted_high = high * multiplier
    mid = base_mid * multiplier * (1 + complexity)

    # Blend mid into range
    final_low = int(round(min(adjusted_low, mid * 0.7)))
    final_high = int(round(max(adjusted_high, mid * 1.4)))

    # Sanity — range should at least be reasonable
    if final_low < 1:
        final_low = int(round(adjusted_low))
    if final_high < final_low + 50:
        final_high = final_low + 100

    factors_used = []
    if multiplier > 1.0:
        factors_used.append(f"regional factor ({state}: {multiplier:.2f}x)")
    if multiplier < 1.0:
        factors_used.append(f"regional discount ({state}: {multiplier:.2f}x)")
    if complexity > 0.1:
        factors_used.append(f"complexity surcharge ({complexity*100:.0f}%)")
    elif complexity < -0.05:
        factors_used.append(f"simplicity discount ({complexity*100:.0f}%)")

    notes = f"Based on: {', '.join(factors_used)}." if factors_used else "Standard pricing."

    return (
        f"**{service.title()} — {zip_code}**\n"
        f"Estimated range: **${final_low:,} – ${final_high:,}**\n"
        f"{notes}"
    )