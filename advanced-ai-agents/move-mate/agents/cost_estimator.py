"""Cost Estimator Agent — estimates moving costs based on household size and distance."""

from models import MoveDetails, CostEstimate


# Base cost estimates by household size (USD 2025)
SIZE_COST_BASES = {
    "studio": {"truck": 40, "supplies": 60, "movers": 200, "travel": 30},
    "1br": {"truck": 60, "supplies": 100, "movers": 400, "travel": 40},
    "2br": {"truck": 100, "supplies": 150, "movers": 700, "travel": 60},
    "3br": {"truck": 150, "supplies": 200, "movers": 1200, "travel": 80},
    "house": {"truck": 200, "supplies": 300, "movers": 2000, "travel": 100},
}

# Distance multiplier (floored zip-code distance approximation)
SHORT_DISTANCE_MULTIPLIER = 1.0    # same city
MEDIUM_DISTANCE_MULTIPLIER = 1.3   # different city in same region
LONG_DISTANCE_MULTIPLIER = 2.0     # cross-country


def _estimate_distance_miles(zip1: str, zip2: str) -> tuple[int, float]:
    """
    Rough distance estimation based on first digit of zip code.
    US zip code regions: 0=NE, 1=SE, 2=Mid-Atlantic, 3=SE, 4=Midwest,
    5=MW/Plains, 6=Central, 7=South, 8=West, 9=West Coast.
    """
    if zip1 == zip2:
        return 0, SHORT_DISTANCE_MULTIPLIER
    try:
        first1 = int(zip1[0])
        first2 = int(zip2[0])
    except (IndexError, ValueError):
        return 50, SHORT_DISTANCE_MULTIPLIER

    diff = abs(first1 - first2)
    if diff == 0:
        return 30, SHORT_DISTANCE_MULTIPLIER
    elif diff <= 2:
        return 100, MEDIUM_DISTANCE_MULTIPLIER
    else:
        return 500, LONG_DISTANCE_MULTIPLIER


def run(details: MoveDetails) -> CostEstimate:
    """Estimate moving costs."""
    estimate = CostEstimate()

    bases = SIZE_COST_BASES.get(details.household_size, SIZE_COST_BASES["1br"])
    distance_miles, multiplier = _estimate_distance_miles(
        details.current_zip, details.new_zip
    )

    # Truck rental: base + distance component
    estimate.truck_rental = round(bases["truck"] + (distance_miles * 1.5), 0)

    # Moving supplies (boxes, tape, wrap, labels)
    estimate.moving_supplies = round(bases["supplies"] * 1.0, 0)

    # Movers/labor (if applicable)
    estimate.movers = round(bases["movers"] * multiplier, 0)

    # Security deposit (if renting)
    if details.is_renting:
        estimate.security_deposit = round(1500.0 * (1 if details.household_size in ["studio", "1br"] else 1.5), 0)
    else:
        estimate.security_deposit = 0.0

    # Cleaning
    estimate.cleaning = round(bases["truck"] * 2.5, 0)

    # Travel costs (gas/fuel, tolls)
    estimate.travel = round(bases["travel"] * multiplier * (distance_miles / 50 if distance_miles > 0 else 1), 0)

    # Notes
    estimate.notes = [
        f"Estimated moving distance: ~{distance_miles} miles (zip-based approximation)",
        "Costs are estimates only — get 3 quotes from moving companies for accurate pricing.",
        "Truck rental estimate based on U-Haul/Budget/Penske standard rates.",
        "Consider moving during off-peak (weekday, mid-month) for 20-30% savings.",
        "Moving supply costs include boxes, tape, bubble wrap, and furniture pads.",
    ]

    if details.household_size in ["3br", "house"]:
        estimate.notes.append("Large households: consider full-service movers for heavy items (piano, treadmill, etc.).")

    return estimate