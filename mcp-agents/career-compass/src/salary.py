"""Salary data from BLS API + regional adjustments.

Provides real median wage data per occupation with cost-of-living adjustments.
When BLS_API_KEY is set, data is fetched live from the BLS API. Otherwise
the built-in occupation database is used.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

from .databases import find_cost_of_living, find_occupation_by_title
from .models import SalaryResult

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/series/data/"


def _fetch_bls_wage(series_id: str, api_key: str) -> Optional[dict]:
    """Fetch a single BLS wage series and return the latest annual value."""
    try:
        resp = httpx.post(
            BLS_API_URL,
            json={"seriesid": [series_id], "registrationkey": api_key, "annualaverage": True},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "REQUEST_SUCCEEDED" and data.get("Results"):
            series = data["Results"]["series"][0]
            if series.get("data"):
                return series["data"][0]  # most recent year
    except Exception:
        pass
    return None


def salary_by_role(job_title: str, zip_code: str = "") -> SalaryResult:
    """Get median wage, percentile data, and cost-of-living adjustment.

    Looks up the occupation in the local database first. If a BLS API key
    is configured, also attempts a live fetch for richer data.
    """
    occupation = find_occupation_by_title(job_title)
    if not occupation:
        return SalaryResult(
            occupation=job_title,
            zip_code=zip_code,
            median_wage=0,
            p10_wage=0,
            p90_wage=0,
            cost_of_living_index=100.0,
            adjusted_median_wage=0,
            data_source="not_found",
        )

    # Cost-of-living adjustment
    col = find_cost_of_living(zip_code) if zip_code else None
    col_index = col.index if col else 100.0
    adjusted = round(occupation.median_wage * (100.0 / col_index), 2) if col_index != 100.0 else occupation.median_wage

    # Try live BLS data if key is set
    api_key = os.getenv("BLS_API_KEY", "")
    data_source = "database"

    if api_key:
        # BLS OEWS series IDs are structured: OE_UN_<area>_<soc_without_dot>
        soc_clean = occupation.soc_code.replace("-", "")
        # National series: OE_UN_N00000000_<soc>
        series_id = f"OEUN0000000000{soc_clean}"
        live = _fetch_bls_wage(series_id, api_key)
        if live:
            wage_val = float(live.get("value", 0))
            if wage_val > 0:
                occupation.median_wage = int(wage_val)
                data_source = "bls_api_live"

    return SalaryResult(
        occupation=occupation.title,
        zip_code=zip_code,
        median_wage=occupation.median_wage,
        p10_wage=occupation.p10_wage,
        p90_wage=occupation.p90_wage,
        cost_of_living_index=col_index,
        adjusted_median_wage=adjusted,
        data_source=data_source,
    )