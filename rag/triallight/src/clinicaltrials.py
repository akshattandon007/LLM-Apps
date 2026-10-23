"""
ClinicalTrials.gov API v2 wrapper — search + fetch live studies.
All endpoints are public, no auth required.
"""
from __future__ import annotations

from typing import Optional

import requests

from .models import EligibilityCriterion, Location, StudyProtocol, StudyStatus

API_BASE = "https://clinicaltrials.gov/api/v2"
SEARCH_URL = f"{API_BASE}/studies"
STUDY_URL = f"{API_BASE}/studies/{{nct_id}}"
_USER_AGENT = "triallight/1.0 (+https://github.com/akshattandon007/LLM-Apps)"

# Status values representing currently-active / enrolling studies
ACTIVE_STATUSES = "RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION"


def search_studies(
    condition: str,
    page_size: int = 10,
    location_query: Optional[str] = None,
) -> dict:
    """Search ClinicalTrials.gov for active studies matching a condition.

    Returns the raw API response dict with study metadata.
    """
    params: dict = {
        "query.cond": condition,
        "pageSize": str(min(page_size, 100)),
        "format": "json",
        "filter.overallStatus": ACTIVE_STATUSES,
    }
    if location_query:
        params["query.locn"] = location_query

    resp = requests.get(
        SEARCH_URL,
        params=params,
        headers={"User-Agent": _USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_study_detail(nct_id: str) -> dict:
    """Fetch full study detail for a given NCT ID."""
    url = STUDY_URL.format(nct_id=nct_id)
    resp = requests.get(
        url,
        params={"format": "json"},
        headers={"User-Agent": _USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def parse_studies(api_response: dict) -> list[StudyProtocol]:
    """Parse the ClinicalTrials.gov v2 API response into StudyProtocol objects."""
    studies: list[StudyProtocol] = []
    raw_studies = api_response.get("studies", [])
    for entry in raw_studies:
        proto = entry.get("protocolSection", {})
        if not proto:
            continue

        ids = proto.get("identificationModule", {})
        desc = proto.get("descriptionModule", {})
        status_mod = proto.get("statusModule", {})
        conds = proto.get("conditionsModule", {})
        eligibility = proto.get("eligibilityModule", {})
        design = proto.get("designModule", {})
        sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
        locs_mod = proto.get("contactsLocationsModule", {})
        locs = locs_mod.get("locations", [])

        nct_id = ids.get("nctId", "")
        if not nct_id:
            continue

        parsed_locations = [
            Location(
                city=loc.get("city", ""),
                state=loc.get("state", ""),
                country=loc.get("country", ""),
                zip=loc.get("zip", loc.get("postalCode", "")),
            )
            for loc in locs
        ]

        # Parse eligibility criteria from free-text
        criteria_text = eligibility.get("eligibilityCriteria", "") or ""
        criteria_list: list[EligibilityCriterion] = []
        current_category = "INCLUSION"
        for line in criteria_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            upper = line.upper()
            if upper.startswith("EXCLUSION CRITERIA") or upper.startswith("EXCLUSION"):
                current_category = "EXCLUSION"
            elif upper.startswith("INCLUSION CRITERIA") or upper.startswith("INCLUSION"):
                current_category = "INCLUSION"
            criteria_list.append(EligibilityCriterion(category=current_category, text=line))

        # Determine status
        overall_status = status_mod.get("overallStatus", "")
        try:
            study_status = StudyStatus(overall_status.replace(" ", "_").upper())
        except ValueError:
            if "ACTIVE" in overall_status:
                study_status = StudyStatus.ACTIVE
            else:
                study_status = StudyStatus.UNKNOWN

        # Conditions
        conditions_raw = conds.get("conditions", [])
        if isinstance(conditions_raw, str):
            conditions_raw = [conditions_raw]

        # Phase
        phases = design.get("phases", [])
        phase_str = ", ".join(phases) if phases else ""

        # Enrollment
        enrollment = design.get("enrollmentInfo", {}).get("count", 0) or 0

        # Lead sponsor
        lead_sponsor_name = ""
        lead_sponsor = sponsor_mod.get("leadSponsor", {})
        if isinstance(lead_sponsor, dict):
            lead_sponsor_name = lead_sponsor.get("name", "")
        elif isinstance(lead_sponsor, str):
            lead_sponsor_name = lead_sponsor

        # Dates
        start_date = status_mod.get("startDateStruct", {}).get("date", "")
        completion_date = status_mod.get("completionDateStruct", {}).get("date", "")

        study = StudyProtocol(
            nct_id=nct_id,
            brief_title=ids.get("briefTitle", ""),
            official_title=ids.get("officialTitle", ""),
            status=study_status,
            conditions=conditions_raw,
            locations=parsed_locations,
            brief_summary=desc.get("briefSummary", ""),
            detailed_description=desc.get("detailedDescription", ""),
            eligibility_criteria=criteria_list,
            enrollment_count=enrollment,
            phase=phase_str,
            start_date=start_date,
            completion_date=completion_date,
            lead_sponsor=lead_sponsor_name,
            url=f"https://clinicaltrials.gov/study/{nct_id}",
        )
        studies.append(study)

    return studies