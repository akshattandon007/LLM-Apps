"""Review sentiment summarization for home service professionals.

In production, this would query Google Reviews, Yelp, Angi, or BBB APIs.
The mock generates plausible summaries based on stored professional data.
"""

import random

from src.service_db import get_pro_by_name


# ── Review templates by rating tier ──────────────────────────────────
_OPENING_TEMPLATES = {
    "excellent": [
        "Customers consistently highlight {name}'s professionalism and prompt service.",
        "{name} enjoys strong word-of-mouth recommendations throughout the community.",
    ],
    "good": [
        "{name} is generally well-regarded, with most customers satisfied with the work quality.",
        "{name} receives solid reviews, particularly for routine service calls.",
    ],
    "mixed": [
        "{name} has a mixed reputation — some customers are delighted, others report inconsistent experiences.",
        "Opinions on {name} are divided. Many praise the workmanship but cite communication issues.",
    ],
    "poor": [
        "{name} has received several complaints about scheduling and pricing transparency.",
        "Customer feedback for {name} flags concerns around responsiveness and follow-through.",
    ],
}

_PROS_TEMPLATES = [
    " Praised for quick response times and clear pricing.",
    " Reviewers note the technicians are knowledgeable and courteous.",
    " Customers appreciate the thorough explanations and upfront estimates.",
    " Service quality is described as reliable and consistent.",
    " Emergency calls are handled with notable speed and professionalism.",
]

_CONS_TEMPLATES = [
    " Some customers report delays during peak seasons.",
    " A few reviews mention that final bills exceeded initial estimates.",
    " Scheduling can be tight — booking a week or more in advance is sometimes necessary.",
    " Occasional complaints about follow-up communication on complex jobs.",
    " A minority of reviewers felt the work was rushed.",
]

_CONCLUSION_TEMPLATES = {
    "excellent": "Highly recommended — a top-tier choice for {service} needs.",
    "good": "A reliable option worth considering for {service} work.",
    "mixed": "Consider getting a second quote and confirming scope in writing.",
    "poor": "Approach with caution — compare multiple quotes and verify credentials carefully.",
}


def _pick_tier(rating: float) -> str:
    """Map a numeric rating to a sentiment tier."""
    if rating >= 4.5:
        return "excellent"
    elif rating >= 4.0:
        return "good"
    elif rating >= 3.0:
        return "mixed"
    else:
        return "poor"


def summarize_reviews(professional: str) -> dict:
    """Generate a review summary for a professional.

    The summary distills key sentiment signals — overall rating, review count,
    recurring praise points, common complaints, and a bottom-line recommendation.
    """
    pro = get_pro_by_name(professional)
    if pro is None:
        return {
            "professional": professional,
            "summary": f"No review data available for '{professional}'.",
            "rating": None,
            "review_count": 0,
            "sentiment": "unknown",
        }

    tier = _pick_tier(pro.rating)
    service_names = [st.value.title() for st in pro.service_types]
    service_str = service_names[0] if len(service_names) == 1 else f"{', '.join(service_names[:-1])} and {service_names[-1]}"

    # Build the summary narrative
    opening = random.choice(_OPENING_TEMPLATES[tier]).format(name=pro.name)

    # Select 1-2 pros points and 0-2 cons points
    pros_list = random.sample(_PROS_TEMPLATES, min(2, len(_PROS_TEMPLATES)))
    if tier in ("excellent", "good"):
        cons_count = min(1, len(_CONS_TEMPLATES))
    elif tier == "mixed":
        cons_count = 2
    else:
        cons_count = min(2, len(_CONS_TEMPLATES))
    cons_list = random.sample(_CONS_TEMPLATES, cons_count)

    closing = _CONCLUSION_TEMPLATES[tier].format(service=service_str)

    summary = opening + "".join(pros_list) + "".join(cons_list) + " " + closing

    return {
        "professional": pro.name,
        "company": pro.company,
        "rating": pro.rating,
        "review_count": pro.review_count,
        "sentiment": tier,
        "summary": summary,
    }