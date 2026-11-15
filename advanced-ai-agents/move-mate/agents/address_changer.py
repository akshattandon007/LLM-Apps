"""Address Changer Agent — lists entities to notify about address change."""

from models import MoveDetails, AddressChangeInfo


def run(details: MoveDetails) -> AddressChangeInfo:
    """Generate address change checklist based on move details."""
    info = AddressChangeInfo()

    # Government (always)
    info.government = [
        "USPS Change of Address (start mail forwarding) — usps.com/move",
        "DMV/DPS — update driver's license address",
        "Voter registration — update with state/county election office",
        "IRS — update address for tax purposes",
        "Social Security Administration — update if receiving benefits",
    ]

    # Financial
    info.financial = [
        "Banks — update address in online banking or branch",
        "Credit card companies — update for all cards",
        "Employer payroll/HR — update direct deposit and W-2 address",
        "Student loans / loan servicer — if applicable",
        "Investment/brokerage accounts — update contact info",
    ]

    # Subscriptions
    info.subscriptions = [
        "Amazon / online shopping accounts — update default address",
        "Streaming services (Netflix, Spotify, etc.) — update billing zip",
        "Meal kit services (HelloFresh, Blue Apron, etc.)",
        "Magazine/newsletter subscriptions",
        "Pharmacy / prescription delivery service",
    ]

    # Insurance
    info.insurance = [
        "Health insurance provider — update address for claims/ID cards",
        "Auto insurance — update garaging address (rate may change)",
        "Renters/Homeowners insurance — update policy (critical!)",
    ]

    # Other
    info.other = [
        "AAA / roadside assistance — update address",
        "Professional licenses / certifications — update address",
        "Doctor/dentist offices — get records sent to new providers",
        "Veterinarian / pet microchip registry — if applicable",
    ]

    info.notes = [
        "Change your address 2-3 weeks BEFORE moving to catch first-round mailings.",
        "Take photos of important documents before packing them in a moving box.",
        "Keep a 'first-night box' with essentials, ID, meds, phone chargers, and basic toiletries.",
    ]

    if details.is_renting:
        info.other.append(
            "Landlord / property manager — provide forwarding address for deposit return"
        )

    return info