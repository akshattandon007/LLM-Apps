"""Utility Scheduler Agent — figures out which utilities need setup/cancellation."""

from models import MoveDetails, UtilityInfo


# Utility provider lookup tables by state/region (generic guidance)
MAJOR_UTILITIES = {
    "electric": [
        "Contact current provider to schedule disconnection after move-out date",
        "Contact new provider to schedule connection before move-in date",
        "Compare rates at https://www.energy.gov for your new region",
    ],
    "gas": [
        "Contact gas utility to transfer or close account",
        "Request final meter reading on move-out day",
    ],
    "water": [
        "Contact local water department / utility for transfer",
        "Ask about deposit/connection fees for new address",
    ],
    "internet": [
        "Schedule internet/cable transfer or new install 1 week before move-in",
        "Compare providers at new address — check availability",
        "Return equipment (router/modem) on old service disconnection",
    ],
    "trash": [
        "Check trash/recycling pickup schedule at new address",
        "Cancel or transfer old service",
        "Request bins if needed (some cities provide them)",
    ],
}


def run(details: MoveDetails) -> UtilityInfo:
    """Generate utility recommendations based on move details."""
    info = UtilityInfo()

    info.electric = list(MAJOR_UTILITIES["electric"])
    info.gas = list(MAJOR_UTILITIES["gas"])
    info.water = list(MAJOR_UTILITIES["water"])
    info.internet = list(MAJOR_UTILITIES["internet"])
    info.trash = list(MAJOR_UTILITIES["trash"])

    # Household size adjustments
    size_notes = {
        "studio": "Minimal utilities — expect lower deposits and setup fees.",
        "1br": "Standard apartment utilities — small connection fees.",
        "2br": "Moderate utility usage — may need 100A electrical service.",
        "3br": "Larger home — budget for higher deposits and seasonal usage.",
        "house": "House — may have separate garbage/water bills from city, well/septic considerations.",
    }
    note = size_notes.get(details.household_size, "")
    if note:
        info.notes.append(note)

    if details.is_renting:
        info.notes.append(
            "Renter: Check lease for which utilities are included in rent "
            "(often water/trash in apartment buildings)."
        )

    info.notes.append(
        "Pro tip: Take photos of all utility meters on move-out and move-in days "
        "to avoid billing disputes."
    )

    return info