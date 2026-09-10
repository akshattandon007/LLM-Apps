"""Growing industries and job outlook data.

Provides data-driven insights on which industries are expanding,
projected job counts, and key hiring regions across the US.
"""

from __future__ import annotations

from .databases import get_all_occupations
from .models import (
    GrowthOutlook,
    IndustryOutlook,
    IndustryResult,
    JobOutlookResult,
)

# ── Industry Outlook Database ──────────────────────────────────────────────────
# Data sourced from BLS Employment Projections 2022-2032.

INDUSTRY_DATA: dict[str, IndustryOutlook] = {
    "541713": IndustryOutlook(
        naics_code="541713",
        industry_name="Software Publishing & Data Processing",
        projected_growth_rate=0.28,
        projected_jobs_added=589_900,
        current_employment=2_580_000,
        key_regions=["San Francisco", "Seattle", "New York", "Austin", "Boston"],
        top_occupations=["Software Developer", "Data Scientist", "Quality Assurance Engineer"],
    ),
    "621111": IndustryOutlook(
        naics_code="621111",
        industry_name="Healthcare Services",
        projected_growth_rate=0.13,
        projected_jobs_added=1_800_000,
        current_employment=15_300_000,
        key_regions=["Houston", "New York", "Chicago", "Los Angeles", "Atlanta"],
        top_occupations=["Registered Nurse", "Physician", "Medical Assistant", "Mental Health Counselor"],
    ),
    "624120": IndustryOutlook(
        naics_code="624120",
        industry_name="Mental Health & Substance Abuse Services",
        projected_growth_rate=0.18,
        projected_jobs_added=95_000,
        current_employment=560_000,
        key_regions=["Boston", "Los Angeles", "Denver", "Portland", "Seattle"],
        top_occupations=["Mental Health Counselor", "Social Worker", "Psychologist"],
    ),
    "518210": IndustryOutlook(
        naics_code="518210",
        industry_name="Data Hosting & Related Services (Cloud)",
        projected_growth_rate=0.22,
        projected_jobs_added=76_000,
        current_employment=380_000,
        key_regions=["Seattle", "San Francisco", "Phoenix", "Dallas", "Northern Virginia"],
        top_occupations=["Cloud Architect", "Network Administrator", "Systems Engineer", "Data Scientist"],
    ),
    "238990": IndustryOutlook(
        naics_code="238990",
        industry_name="Renewable Energy Construction",
        projected_growth_rate=0.14,
        projected_jobs_added=140_000,
        current_employment=950_000,
        key_regions=["Houston", "Denver", "Phoenix", "Los Angeles", "Midwest"],
        top_occupations=["Civil Engineer", "Electrical Engineer", "Project Manager", "Maintenance Worker"],
    ),
    "334413": IndustryOutlook(
        naics_code="334413",
        industry_name="Semiconductor & Electronics Manufacturing",
        projected_growth_rate=0.08,
        projected_jobs_added=40_000,
        current_employment=520_000,
        key_regions=["Phoenix", "Austin", "Portland", "San Jose", "Dallas"],
        top_occupations=["Electronics Engineer", "Production Supervisor", "Quality Control Analyst"],
    ),
    "531110": IndustryOutlook(
        naics_code="531110",
        industry_name="FinTech & Financial Services",
        projected_growth_rate=0.06,
        projected_jobs_added=110_000,
        current_employment=1_900_000,
        key_regions=["New York", "San Francisco", "Chicago", "Charlotte", "Dallas"],
        top_occupations=["Software Developer", "Accountant", "Market Research Analyst", "Info Security Analyst"],
    ),
    "611310": IndustryOutlook(
        naics_code="611310",
        industry_name="Online Education & EdTech",
        projected_growth_rate=0.10,
        projected_jobs_added=55_000,
        current_employment=520_000,
        key_regions=["New York", "San Francisco", "Boston", "Austin", "Los Angeles"],
        top_occupations=["Instructional Designer", "Software Developer", "Marketing Manager"],
    ),
}


def growing_industries(region: str = "") -> IndustryResult:
    """Get projected growth sectors with real job counts.

    Filters by region if provided, otherwise returns all growing industries
    sorted by projected growth rate descending.
    """
    industries = list(INDUSTRY_DATA.values())
    industries.sort(key=lambda x: x.projected_growth_rate, reverse=True)

    if region:
        region_lower = region.lower()
        filtered = []
        for ind in industries:
            for kr in ind.key_regions:
                if region_lower in kr.lower():
                    filtered.append(ind)
                    break
        industries = filtered

    return IndustryResult(
        region=region or "National (all regions)",
        industries=industries[:8],  # top 8 results
        data_source="database",
    )


def job_outlook(occupation_title: str, region: str = "") -> JobOutlookResult:
    """Get projected demand, growth rate, and key hiring areas.

    Estimates the future demand for a given occupation by cross-referencing
    the occupation database with industry growth data.
    """
    from .databases import find_occupation_by_title

    occ = find_occupation_by_title(occupation_title)

    if not occ:
        return JobOutlookResult(
            occupation=occupation_title,
            region=region or "National",
            current_employment=0,
            projected_growth_rate=0.0,
            growth_outlook=GrowthOutlook.LITTLE_CHANGE,
            annual_openings=0,
            key_industries=[],
            data_source="not_found",
        )

    # Determine growth classification
    if occ.growth_rate >= 0.20:
        outlook = GrowthOutlook.VERY_FAST
    elif occ.growth_rate >= 0.10:
        outlook = GrowthOutlook.FAST_GROWING
    elif occ.growth_rate >= 0.05:
        outlook = GrowthOutlook.GROWING
    elif occ.growth_rate >= -0.02:
        outlook = GrowthOutlook.LITTLE_CHANGE
    else:
        outlook = GrowthOutlook.DECLINE

    # Find which industries employ this occupation
    occ_lower = occ.title.lower()
    key_industries = []
    for ind in INDUSTRY_DATA.values():
        for top_occ in ind.top_occupations:
            if occ_lower in top_occ.lower():
                key_industries.append(ind.industry_name)
                break

    return JobOutlookResult(
        occupation=occ.title,
        region=region or "National",
        current_employment=occ.openings_year * (1 - occ.growth_rate if occ.growth_rate < 0 else 1),
        projected_growth_rate=occ.growth_rate,
        growth_outlook=outlook,
        annual_openings=occ.openings_year,
        key_industries=key_industries if key_industries else ["General (multiple industries)"],
        data_source="database",
    )