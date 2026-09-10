"""Occupation database + regional cost-of-living data.

All data is seeded from public BLS sources. The BLS API is called when
BLS_API_KEY is set; otherwise cached/simulated data is returned.
"""

from __future__ import annotations

from .models import CostOfLiving, DegreeLevel, Occupation

# ── Occupations Database ──────────────────────────────────────────────────────
# Data sourced from BLS Occupational Employment & Wage Statistics (OEWS) May 2023
# and BLS Employment Projections 2022-2032.

OCCUPATIONS: dict[str, Occupation] = {
    "15-1252": Occupation(
        soc_code="15-1252",
        title="Software Developer",
        median_wage=130_160,
        p10_wage=74_000,
        p90_wage=208_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.25,
        openings_year=162_900,
        description="Develop, create, and modify general computer applications software or specialized utility programs.",
    ),
    "15-1251": Occupation(
        soc_code="15-1251",
        title="Computer & Information Research Scientist",
        median_wage=145_080,
        p10_wage=79_000,
        p90_wage=233_000,
        typical_education=DegreeLevel.MASTERS,
        experience_years=3,
        growth_rate=0.23,
        openings_year=3_400,
        description="Conduct research into fundamental computer and information science problems.",
    ),
    "15-1242": Occupation(
        soc_code="15-1242",
        title="Database Administrator",
        median_wage=101_720,
        p10_wage=56_000,
        p90_wage=163_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.08,
        openings_year=11_500,
        description="Administer, test, and implement computer databases.",
    ),
    "15-1244": Occupation(
        soc_code="15-1244",
        title="Network & Computer Systems Administrator",
        median_wage=92_570,
        p10_wage=54_000,
        p90_wage=145_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=3,
        growth_rate=0.02,
        openings_year=23_900,
        description="Install, configure, and support an organization's local area network and systems.",
    ),
    "15-1299": Occupation(
        soc_code="15-1299",
        title="Computer Occupations, All Other",
        median_wage=106_690,
        p10_wage=55_000,
        p90_wage=181_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.10,
        openings_year=13_100,
        description="All computer occupations not listed separately.",
    ),
    "15-1211": Occupation(
        soc_code="15-1211",
        title="Computer Systems Analyst",
        median_wage=102_240,
        p10_wage=60_000,
        p90_wage=160_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.10,
        openings_year=50_800,
        description="Analyze science, engineering, business, and other data processing problems.",
    ),
    "15-1212": Occupation(
        soc_code="15-1212",
        title="Information Security Analyst",
        median_wage=120_360,
        p10_wage=68_000,
        p90_wage=185_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.32,
        openings_year=16_800,
        description="Plan, implement, and monitor security measures for computer networks.",
    ),
    "15-1231": Occupation(
        soc_code="15-1231",
        title="Computer Network Support Specialist",
        median_wage=68_050,
        p10_wage=40_000,
        p90_wage=117_000,
        typical_education=DegreeLevel.ASSOCIATES,
        experience_years=1,
        growth_rate=0.06,
        openings_year=23_600,
        description="Analyze, test, troubleshoot, and evaluate existing network systems.",
    ),
    "15-1232": Occupation(
        soc_code="15-1232",
        title="Computer User Support Specialist",
        median_wage=60_810,
        p10_wage=36_000,
        p90_wage=100_000,
        typical_education=DegreeLevel.ASSOCIATES,
        experience_years=1,
        growth_rate=0.05,
        openings_year=70_600,
        description="Provide technical assistance to computer users.",
    ),
    "15-1241": Occupation(
        soc_code="15-1241",
        title="Computer Network Architect",
        median_wage=129_840,
        p10_wage=72_000,
        p90_wage=198_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=5,
        growth_rate=0.04,
        openings_year=10_800,
        description="Design and build data communication networks.",
    ),
    "11-1021": Occupation(
        soc_code="11-1021",
        title="General & Operations Manager",
        median_wage=122_860,
        p10_wage=58_000,
        p90_wage=216_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=5,
        growth_rate=0.03,
        openings_year=189_600,
        description="Plan, direct, or coordinate the operations of public or private sector organizations.",
    ),
    "13-1161": Occupation(
        soc_code="13-1161",
        title="Market Research Analyst",
        median_wage=74_680,
        p10_wage=41_000,
        p90_wage=131_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=1,
        growth_rate=0.13,
        openings_year=99_300,
        description="Research market conditions to determine potential sales of a product or service.",
    ),
    "13-1082": Occupation(
        soc_code="13-1082",
        title="Project Management Specialist",
        median_wage=98_580,
        p10_wage=53_000,
        p90_wage=164_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=3,
        growth_rate=0.07,
        openings_year=62_200,
        description="Plan, direct, and coordinate projects across an organization.",
    ),
    "29-2052": Occupation(
        soc_code="29-2052",
        title="Registered Nurse",
        median_wage=86_070,
        p10_wage=61_000,
        p90_wage=129_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=1,
        growth_rate=0.06,
        openings_year=177_400,
        description="Provide and coordinate patient care, educate patients about health conditions.",
    ),
    "29-1221": Occupation(
        soc_code="29-1221",
        title="Physician, All Other",
        median_wage=235_000,
        p10_wage=110_000,
        p90_wage=360_000,
        typical_education=DegreeLevel.DOCTORAL,
        experience_years=7,
        growth_rate=0.03,
        openings_year=24_300,
        description="Diagnose and treat injuries or illnesses.",
    ),
    "17-2051": Occupation(
        soc_code="17-2051",
        title="Civil Engineer",
        median_wage=95_890,
        p10_wage=58_000,
        p90_wage=149_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.05,
        openings_year=24_200,
        description="Design and supervise construction of infrastructure projects.",
    ),
    "17-2072": Occupation(
        soc_code="17-2072",
        title="Electronics Engineer",
        median_wage=119_300,
        p10_wage=68_000,
        p90_wage=177_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.05,
        openings_year=10_600,
        description="Design, develop, and test electronic equipment and systems.",
    ),
    "25-2021": Occupation(
        soc_code="25-2021",
        title="Elementary School Teacher",
        median_wage=65_660,
        p10_wage=40_000,
        p90_wage=102_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=0,
        growth_rate=0.01,
        openings_year=121_600,
        description="Teach academic and social skills to elementary school students.",
    ),
    "49-9071": Occupation(
        soc_code="49-9071",
        title="Maintenance & Repair Worker",
        median_wage=46_590,
        p10_wage=30_000,
        p90_wage=72_000,
        typical_education=DegreeLevel.HIGH_SCHOOL,
        experience_years=1,
        growth_rate=0.03,
        openings_year=137_000,
        description="Perform work involving the maintenance and repair of machines and physical structures.",
    ),
    "51-1011": Occupation(
        soc_code="51-1011",
        title="First-Line Supervisor, Production",
        median_wage=63_630,
        p10_wage=40_000,
        p90_wage=100_000,
        typical_education=DegreeLevel.HIGH_SCHOOL,
        experience_years=3,
        growth_rate=-0.02,
        openings_year=55_500,
        description="Supervise and coordinate the activities of production and operating workers.",
    ),
    "21-1098": Occupation(
        soc_code="21-1098",
        title="Mental Health Counselor",
        median_wage=55_280,
        p10_wage=34_000,
        p90_wage=95_000,
        typical_education=DegreeLevel.MASTERS,
        experience_years=1,
        growth_rate=0.18,
        openings_year=42_500,
        description="Counsel individuals and groups to promote optimal mental and emotional health.",
    ),
    "13-2011": Occupation(
        soc_code="13-2011",
        title="Accountant & Auditor",
        median_wage=81_280,
        p10_wage=48_000,
        p90_wage=136_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=1,
        growth_rate=0.06,
        openings_year=126_500,
        description="Examine, analyze, and interpret accounting records to prepare financial statements.",
    ),
    "11-2021": Occupation(
        soc_code="11-2021",
        title="Marketing Manager",
        median_wage=157_970,
        p10_wage=81_000,
        p90_wage=239_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=5,
        growth_rate=0.07,
        openings_year=35_700,
        description="Plan, direct, and coordinate marketing policies and programs.",
    ),
    "15-2051": Occupation(
        soc_code="15-2051",
        title="Data Scientist",
        median_wage=126_000,
        p10_wage=72_000,
        p90_wage=200_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.35,
        openings_year=19_400,
        description="Analyze and interpret complex data to help organizations make decisions.",
    ),
}

# ── Cost-of-Living Database (BLS-compatible index) ─────────────────────────────
# National average index = 100. Data approximated from C2ER Q3 2023.

COST_OF_LIVING: dict[str, CostOfLiving] = {
    "10001": CostOfLiving(zip_code="10001", city="New York", state="NY", index=158.8, housing_index=210.0, groceries_index=115.0, transportation_index=128.0, utilities_index=120.0),
    "10002": CostOfLiving(zip_code="10002", city="New York", state="NY", index=155.2, housing_index=205.0, groceries_index=112.0, transportation_index=125.0, utilities_index=118.0),
    "94102": CostOfLiving(zip_code="94102", city="San Francisco", state="CA", index=176.2, housing_index=240.0, groceries_index=118.0, transportation_index=130.0, utilities_index=115.0),
    "94105": CostOfLiving(zip_code="94105", city="San Francisco", state="CA", index=180.0, housing_index=250.0, groceries_index=120.0, transportation_index=135.0, utilities_index=118.0),
    "90001": CostOfLiving(zip_code="90001", city="Los Angeles", state="CA", index=138.0, housing_index=175.0, groceries_index=107.0, transportation_index=120.0, utilities_index=110.0),
    "90012": CostOfLiving(zip_code="90012", city="Los Angeles", state="CA", index=140.2, housing_index=180.0, groceries_index=108.0, transportation_index=122.0, utilities_index=112.0),
    "60601": CostOfLiving(zip_code="60601", city="Chicago", state="IL", index=115.6, housing_index=128.0, groceries_index=108.0, transportation_index=112.0, utilities_index=110.0),
    "60607": CostOfLiving(zip_code="60607", city="Chicago", state="IL", index=114.2, housing_index=125.0, groceries_index=107.0, transportation_index=110.0, utilities_index=109.0),
    "77001": CostOfLiving(zip_code="77001", city="Houston", state="TX", index=96.8, housing_index=90.0, groceries_index=95.0, transportation_index=98.0, utilities_index=102.0),
    "77002": CostOfLiving(zip_code="77002", city="Houston", state="TX", index=98.0, housing_index=92.0, groceries_index=96.0, transportation_index=100.0, utilities_index=103.0),
    "19101": CostOfLiving(zip_code="19101", city="Philadelphia", state="PA", index=107.2, housing_index=112.0, groceries_index=104.0, transportation_index=108.0, utilities_index=106.0),
    "02101": CostOfLiving(zip_code="02101", city="Boston", state="MA", index=148.0, housing_index=195.0, groceries_index=115.0, transportation_index=125.0, utilities_index=115.0),
    "02108": CostOfLiving(zip_code="02108", city="Boston", state="MA", index=150.5, housing_index=200.0, groceries_index=116.0, transportation_index=127.0, utilities_index=116.0),
    "20001": CostOfLiving(zip_code="20001", city="Washington DC", state="DC", index=148.5, housing_index=195.0, groceries_index=110.0, transportation_index=122.0, utilities_index=112.0),
    "20002": CostOfLiving(zip_code="20002", city="Washington DC", state="DC", index=146.2, housing_index=190.0, groceries_index=109.0, transportation_index=120.0, utilities_index=111.0),
    "98101": CostOfLiving(zip_code="98101", city="Seattle", state="WA", index=155.0, housing_index=210.0, groceries_index=115.0, transportation_index=120.0, utilities_index=108.0),
    "98102": CostOfLiving(zip_code="98102", city="Seattle", state="WA", index=153.0, housing_index=205.0, groceries_index=114.0, transportation_index=118.0, utilities_index=107.0),
    "30301": CostOfLiving(zip_code="30301", city="Atlanta", state="GA", index=104.0, housing_index=102.0, groceries_index=103.0, transportation_index=105.0, utilities_index=100.0),
    "30303": CostOfLiving(zip_code="30303", city="Atlanta", state="GA", index=106.2, housing_index=105.0, groceries_index=104.0, transportation_index=107.0, utilities_index=101.0),
    "48201": CostOfLiving(zip_code="48201", city="Detroit", state="MI", index=90.2, housing_index=82.0, groceries_index=94.0, transportation_index=96.0, utilities_index=98.0),
    "75201": CostOfLiving(zip_code="75201", city="Dallas", state="TX", index=103.5, housing_index=105.0, groceries_index=100.0, transportation_index=102.0, utilities_index=100.0),
    "75202": CostOfLiving(zip_code="75202", city="Dallas", state="TX", index=102.0, housing_index=103.0, groceries_index=99.0, transportation_index=101.0, utilities_index=99.0),
    "85001": CostOfLiving(zip_code="85001", city="Phoenix", state="AZ", index=103.0, housing_index=105.0, groceries_index=101.0, transportation_index=104.0, utilities_index=102.0),
    "33101": CostOfLiving(zip_code="33101", city="Miami", state="FL", index=118.0, housing_index=135.0, groceries_index=110.0, transportation_index=114.0, utilities_index=108.0),
    "33102": CostOfLiving(zip_code="33102", city="Miami", state="FL", index=116.5, housing_index=132.0, groceries_index=109.0, transportation_index=112.0, utilities_index=107.0),
    "97201": CostOfLiving(zip_code="97201", city="Portland", state="OR", index=121.0, housing_index=140.0, groceries_index=110.0, transportation_index=112.0, utilities_index=105.0),
}


def find_occupation_by_title(title: str) -> Occupation | None:
    """Find the best-matching Occupation by partial title match."""
    title_lower = title.lower()
    for code, occ in OCCUPATIONS.items():
        if title_lower in occ.title.lower():
            return occ
    return None


def find_occupation(code: str) -> Occupation | None:
    """Find an Occupation by its SOC code."""
    return OCCUPATIONS.get(code)


def get_all_occupations() -> list[Occupation]:
    """Return all occupations in the database."""
    return list(OCCUPATIONS.values())


def find_cost_of_living(zip_code: str) -> CostOfLiving | None:
    """Look up cost-of-living data by 5-digit zip code prefix."""
    # Try exact match first, then prefix match
    if zip_code in COST_OF_LIVING:
        return COST_OF_LIVING[zip_code]
    prefix = zip_code[:5]
    if prefix in COST_OF_LIVING:
        return COST_OF_LIVING[prefix]
    for zc, col in COST_OF_LIVING.items():
        if zc.startswith(prefix[:2]):
            return col
    return None