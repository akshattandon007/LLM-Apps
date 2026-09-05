"""Find service professionals by type and location with filtering."""

from src.models import ServiceType, Pro
from src.service_db import get_pros_by_service, get_pro_by_name


def find_pros(service_type: str, zip_code: str, emergency: bool = False) -> list[dict]:
    """Find licensed, available pros matching service type and location.

    Results sorted by rating descending. Optionally filters to emergency-available pros.
    Returns serializable dicts.
    """
    try:
        st = ServiceType(service_type.lower())
    except ValueError:
        return []

    pros = get_pros_by_service(st)

    # Filter by ZIP prefix (area match)
    zip_prefix = zip_code[:3]
    pros = [p for p in pros if p.zip_code[:3] == zip_prefix or p.zip_code == zip_code]

    if emergency:
        pros = [p for p in pros if p.available_now]

    # Build response
    results = []
    for p in pros:
        results.append({
            "name": p.name,
            "company": p.company,
            "service_types": [st.value for st in p.service_types],
            "phone": p.phone,
            "zip_code": p.zip_code,
            "rating": p.rating,
            "review_count": p.review_count,
            "years_in_business": p.years_in_business,
            "licensed": p.licensed,
            "insured": p.insured,
            "bonded": p.bonded,
            "available_now": p.available_now,
        })

    return results


def get_pro_details(name: str) -> dict | None:
    """Get details for a specific professional by name."""
    pro = get_pro_by_name(name)
    if pro is None:
        return None
    return {
        "name": pro.name,
        "company": pro.company,
        "service_types": [st.value for st in pro.service_types],
        "phone": pro.phone,
        "zip_code": pro.zip_code,
        "rating": pro.rating,
        "review_count": pro.review_count,
        "years_in_business": pro.years_in_business,
        "licensed": pro.licensed,
        "insured": pro.insured,
        "bonded": pro.bonded,
        "available_now": pro.available_now,
    }