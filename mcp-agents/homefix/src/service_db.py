"""Service type definitions, common pricing data, and a mock professional database."""

from src.models import ServiceType, ServiceDefinition, Pro


# ── Service definitions ──────────────────────────────────────────────
SERVICE_DEFINITIONS: dict[ServiceType, ServiceDefinition] = {
    ServiceType.plumber: ServiceDefinition(
        service_type=ServiceType.plumber,
        display_name="Plumber",
        common_issues=[
            "Burst pipe", "Clogged drain", "Leaky faucet",
            "Water heater failure", "Sewer backup", "Running toilet",
        ],
        typical_price_range="$150 – $800",
        urgent=True,
        requires_license_check=True,
    ),
    ServiceType.electrician: ServiceDefinition(
        service_type=ServiceType.electrician,
        display_name="Electrician",
        common_issues=[
            "Tripping breaker", "Dead outlet", "Flickering lights",
            "Wiring upgrade", "Panel replacement", "GFCI installation",
        ],
        typical_price_range="$200 – $1,200",
        urgent=True,
        requires_license_check=True,
    ),
    ServiceType.hvac: ServiceDefinition(
        service_type=ServiceType.hvac,
        display_name="HVAC Technician",
        common_issues=[
            "AC not cooling", "Heater not working", "Thermostat issues",
            "Refrigerant leak", "Duct cleaning", "Compressor failure",
        ],
        typical_price_range="$300 – $2,500",
        urgent=True,
        requires_license_check=True,
    ),
    ServiceType.handyman: ServiceDefinition(
        service_type=ServiceType.handyman,
        display_name="Handyman",
        common_issues=[
            "Drywall repair", "Furniture assembly", "Painting",
            "Caulking", "Door adjustment", "Gutter cleaning",
        ],
        typical_price_range="$100 – $600",
        urgent=False,
        requires_license_check=False,
    ),
    ServiceType.locksmith: ServiceDefinition(
        service_type=ServiceType.locksmith,
        display_name="Locksmith",
        common_issues=[
            "Locked out", "Broken key", "Lock rekey",
            "Deadbolt installation", "Safe opening", "Smart lock setup",
        ],
        typical_price_range="$75 – $400",
        urgent=True,
        requires_license_check=True,
    ),
    ServiceType.general_contractor: ServiceDefinition(
        service_type=ServiceType.general_contractor,
        display_name="General Contractor",
        common_issues=[
            "Kitchen remodel", "Bathroom renovation", "Deck building",
            "Roof repair", "Foundation work", "Home addition",
        ],
        typical_price_range="$5,000 – $50,000+",
        urgent=False,
        requires_license_check=True,
    ),
}


# ── Regional pricing modifiers (multipliers relative to baseline) ────
REGIONAL_PRICING: dict[str, dict[str, float]] = {
    "NY": {"plumber": 1.35, "electrician": 1.30, "hvac": 1.25, "handyman": 1.20, "locksmith": 1.15, "general_contractor": 1.30},
    "CA": {"plumber": 1.40, "electrician": 1.35, "hvac": 1.30, "handyman": 1.25, "locksmith": 1.20, "general_contractor": 1.35},
    "TX": {"plumber": 1.05, "electrician": 1.05, "hvac": 1.00, "handyman": 1.00, "locksmith": 0.95, "general_contractor": 1.05},
    "FL": {"plumber": 1.10, "electrician": 1.10, "hvac": 1.10, "handyman": 1.00, "locksmith": 1.00, "general_contractor": 1.10},
    "IL": {"plumber": 1.20, "electrician": 1.20, "hvac": 1.15, "handyman": 1.10, "locksmith": 1.05, "general_contractor": 1.20},
}

# Default multiplier when state not found
DEFAULT_REGIONAL_MULTIPLIER = 1.0

# Baseline price ranges by service type (low, high)
BASELINE_PRICES: dict[str, tuple[int, int]] = {
    "plumber": (150, 800),
    "electrician": (200, 1200),
    "hvac": (300, 2500),
    "handyman": (100, 600),
    "locksmith": (75, 400),
    "general_contractor": (5000, 50000),
}

# Urgency surcharge (% of baseline added for emergency dispatch)
URGENCY_SURCHARGE = 0.25


# ── Mock professional database ───────────────────────────────────────
MOCK_PROS: list[Pro] = [
    Pro(name="Rapid Rooter Plumbing", company="Rapid Rooter LLC",
        service_types=[ServiceType.plumber], phone="+1-555-0101",
        zip_code="10001", rating=4.7, review_count=203,
        years_in_business=12, licensed=True, insured=True, bonded=True,
        available_now=True),
    Pro(name="Fix-a-Pipe 24/7", company="Fix-a-Pipe Inc",
        service_types=[ServiceType.plumber], phone="+1-555-0102",
        zip_code="10002", rating=4.3, review_count=87,
        years_in_business=5, licensed=True, insured=True, bonded=False,
        available_now=True),
    Pro(name="BrightSpark Electric", company="BrightSpark Co",
        service_types=[ServiceType.electrician], phone="+1-555-0103",
        zip_code="10001", rating=4.8, review_count=312,
        years_in_business=18, licensed=True, insured=True, bonded=True,
        available_now=True),
    Pro(name="WireWise Electric", company="WireWise Services",
        service_types=[ServiceType.electrician], phone="+1-555-0104",
        zip_code="10003", rating=4.2, review_count=56,
        years_in_business=3, licensed=True, insured=True, bonded=False,
        available_now=True),
    Pro(name="ClimatePro HVAC", company="ClimatePro Systems",
        service_types=[ServiceType.hvac], phone="+1-555-0105",
        zip_code="10001", rating=4.6, review_count=178,
        years_in_business=10, licensed=True, insured=True, bonded=True,
        available_now=True),
    Pro(name="CoolBreeze AC & Heat", company="CoolBreeze Services",
        service_types=[ServiceType.hvac], phone="+1-555-0106",
        zip_code="10002", rating=4.1, review_count=44,
        years_in_business=4, licensed=True, insured=True, bonded=False,
        available_now=True),
    Pro(name="Ace Handyman Services", company="Ace Handyman LLC",
        service_types=[ServiceType.handyman], phone="+1-555-0107",
        zip_code="10001", rating=4.4, review_count=95,
        years_in_business=7, licensed=False, insured=True, bonded=False,
        available_now=False),
    Pro(name="Mr. FixIt Pro", company="Mr. FixIt LLC",
        service_types=[ServiceType.handyman], phone="+1-555-0108",
        zip_code="10002", rating=4.0, review_count=32,
        years_in_business=2, licensed=False, insured=False, bonded=False,
        available_now=False),
    Pro(name="KeyMaster Locksmith", company="KeyMaster Inc",
        service_types=[ServiceType.locksmith], phone="+1-555-0109",
        zip_code="10001", rating=4.9, review_count=411,
        years_in_business=22, licensed=True, insured=True, bonded=True,
        available_now=True),
    Pro(name="LockOut Rescue", company="LockOut Rescue LLC",
        service_types=[ServiceType.locksmith], phone="+1-555-0110",
        zip_code="10003", rating=4.5, review_count=67,
        years_in_business=6, licensed=True, insured=True, bonded=False,
        available_now=True),
    Pro(name="BuildRight Contractors", company="BuildRight Inc",
        service_types=[ServiceType.general_contractor], phone="+1-555-0111",
        zip_code="10001", rating=4.5, review_count=88,
        years_in_business=15, licensed=True, insured=True, bonded=True,
        available_now=False),
    Pro(name="Premier Home Builders", company="Premier Home Group",
        service_types=[ServiceType.general_contractor], phone="+1-555-0112",
        zip_code="10002", rating=4.3, review_count=54,
        years_in_business=9, licensed=True, insured=True, bonded=True,
        available_now=False),
]


def get_service_def(service_type: ServiceType) -> ServiceDefinition:
    """Return the definition for a given service type."""
    return SERVICE_DEFINITIONS[service_type]


def get_pros_by_service(service_type: ServiceType) -> list[Pro]:
    """Return mock pros matching a service type, sorted by rating descending."""
    matches = [p for p in MOCK_PROS if service_type in p.service_types]
    return sorted(matches, key=lambda p: p.rating, reverse=True)


def get_pro_by_name(name: str) -> Pro | None:
    """Find a professional by name (case-insensitive partial match)."""
    lower = name.lower()
    for p in MOCK_PROS:
        if lower in p.name.lower() or lower in p.company.lower():
            return p
    return None