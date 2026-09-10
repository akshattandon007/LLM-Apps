"""Career progression mapping.

Provides realistic career step sequences with salary milestones,
typical promotion paths, and timeframes for advancement.
"""

from __future__ import annotations

from .databases import find_occupation_by_title
from .models import CareerPathResult, CareerStep, DegreeLevel

# ── Progression Maps ──────────────────────────────────────────────────────────
# Realistic career ladders for common job families.

PROGRESSION_MAPS: dict[str, list[CareerStep]] = {
    "software": [
        CareerStep(step=1, title="Junior Software Developer", years_to_reach=0, salary_range="60,000 - 85,000", description="Entry-level coding, bug fixes, unit tests under senior guidance.", typical_promotion_path="2-3 years → Developer"),
        CareerStep(step=2, title="Software Developer", years_to_reach=3, salary_range="85,000 - 120,000", description="Independent feature work, code reviews, mentoring juniors.", typical_promotion_path="2-3 years → Senior Developer"),
        CareerStep(step=3, title="Senior Software Developer", years_to_reach=6, salary_range="120,000 - 160,000", description="Architecture decisions, project planning, cross-team coordination.", typical_promotion_path="3-4 years → Staff / Lead"),
        CareerStep(step=4, title="Staff Engineer / Tech Lead", years_to_reach=10, salary_range="160,000 - 210,000", description="Organization-wide technical strategy, mentoring multiple teams.", typical_promotion_path="4-5 years → Principal"),
        CareerStep(step=5, title="Principal Engineer", years_to_reach=15, salary_range="200,000 - 300,000", description="Company technical vision, industry influence, defining best practices.", typical_promotion_path="→ Director / Distinguished"),
    ],
    "data": [
        CareerStep(step=1, title="Junior Data Analyst", years_to_reach=0, salary_range="50,000 - 75,000", description="SQL queries, basic dashboards, report generation.", typical_promotion_path="1-2 years → Analyst"),
        CareerStep(step=2, title="Data Analyst", years_to_reach=2, salary_range="70,000 - 95,000", description="Statistical analysis, A/B tests, stakeholder presentations.", typical_promotion_path="2-3 years → Senior / Data Scientist"),
        CareerStep(step=3, title="Data Scientist", years_to_reach=5, salary_range="100,000 - 140,000", description="ML model development, experiment design, productionizing pipelines.", typical_promotion_path="3-4 years → Senior Data Scientist"),
        CareerStep(step=4, title="Senior Data Scientist", years_to_reach=9, salary_range="140,000 - 190,000", description="Leading research initiatives, mentoring, cross-functional ML strategy.", typical_promotion_path="4-5 years → Staff / Manager"),
        CareerStep(step=5, title="Staff Data Scientist / ML Manager", years_to_reach=14, salary_range="180,000 - 260,000", description="Organizational data strategy, shaping ML platform, team leadership.", typical_promotion_path="→ Director of Data Science"),
    ],
    "security": [
        CareerStep(step=1, title="Junior Security Analyst", years_to_reach=0, salary_range="55,000 - 80,000", description="Log monitoring, incident triage, vulnerability scanning.", typical_promotion_path="2-3 years → Security Analyst"),
        CareerStep(step=2, title="Security Analyst", years_to_reach=3, salary_range="80,000 - 105,000", description="Incident response, compliance audits, security tooling.", typical_promotion_path="2-3 years → Senior Analyst"),
        CareerStep(step=3, title="Senior Security Engineer", years_to_reach=6, salary_range="110,000 - 155,000", description="Architecture security reviews, penetration testing, security automation.", typical_promotion_path="3-4 years → Lead / Architect"),
        CareerStep(step=4, title="Security Architect", years_to_reach=10, salary_range="150,000 - 200,000", description="Enterprise security design, policy creation, vendor evaluation.", typical_promotion_path="4-5 years → CISO / Director"),
        CareerStep(step=5, title="CISO / Director of Security", years_to_reach=15, salary_range="190,000 - 300,000", description="Executive-level security strategy, board reporting, regulatory compliance.", typical_promotion_path="→ VP Security"),
    ],
    "management": [
        CareerStep(step=1, title="Team Lead / Supervisor", years_to_reach=0, salary_range="65,000 - 95,000", description="Direct team oversight, task delegation, performance reviews.", typical_promotion_path="2-3 years → Manager"),
        CareerStep(step=2, title="Department Manager", years_to_reach=3, salary_range="90,000 - 135,000", description="Budget management, hiring, cross-team coordination.", typical_promotion_path="3-4 years → Senior Manager"),
        CareerStep(step=3, title="Senior Manager", years_to_reach=7, salary_range="125,000 - 175,000", description="Multiple team oversight, strategic planning, org-level initiatives.", typical_promotion_path="3-5 years → Director"),
        CareerStep(step=4, title="Director", years_to_reach=11, salary_range="160,000 - 240,000", description="Department strategy, P&L ownership, executive reporting.", typical_promotion_path="4-6 years → VP"),
        CareerStep(step=5, title="Vice President", years_to_reach=16, salary_range="220,000 - 350,000", description="Organization-wide leadership, board interaction, company strategy.", typical_promotion_path="→ C-Suite"),
    ],
    "healthcare": [
        CareerStep(step=1, title="Certified Nursing Assistant / Medical Assistant", years_to_reach=0, salary_range="30,000 - 45,000", description="Patient care support, vitals, administrative tasks.", typical_promotion_path="2 years → LPN / Specialist"),
        CareerStep(step=2, title="Licensed Practical Nurse", years_to_reach=2, salary_range="45,000 - 60,000", description="Direct patient care under RN supervision.", typical_promotion_path="2-3 years → RN (bridge program)"),
        CareerStep(step=3, title="Registered Nurse", years_to_reach=5, salary_range="65,000 - 95,000", description="Independent patient care, care planning, patient education.", typical_promotion_path="2-3 years → Charge Nurse / Specialty"),
        CareerStep(step=4, title="Nurse Practitioner / Clinical Specialist", years_to_reach=8, salary_range="95,000 - 130,000", description="Advanced practice, diagnosis, treatment plans.", typical_promotion_path="3-5 years → Director / Nurse Manager"),
        CareerStep(step=5, title="Director of Nursing / Healthcare Admin", years_to_reach=13, salary_range="120,000 - 180,000", description="Nursing department strategy, quality improvement, regulatory compliance.", typical_promotion_path="→ CNO / COO"),
    ],
    "education": [
        CareerStep(step=1, title="Teaching Assistant / Paraprofessional", years_to_reach=0, salary_range="25,000 - 38,000", description="Classroom support, small group instruction, material prep.", typical_promotion_path="1-2 years → Teacher"),
        CareerStep(step=2, title="Classroom Teacher", years_to_reach=2, salary_range="42,000 - 68,000", description="Full teaching load, lesson planning, parent communication.", typical_promotion_path="3-5 years → Senior / Lead"),
        CareerStep(step=3, title="Lead Teacher / Department Head", years_to_reach=7, salary_range="55,000 - 85,000", description="Curriculum coordination, teacher mentoring, department budget.", typical_promotion_path="3-5 years → Administrator"),
        CareerStep(step=4, title="Instructional Coordinator / Principal", years_to_reach=12, salary_range="75,000 - 120,000", description="School-wide instructional strategy, staff evaluation, community relations.", typical_promotion_path="5-7 years → District Admin"),
        CareerStep(step=5, title="District Administrator / Superintendent", years_to_reach=18, salary_range="100,000 - 180,000", description="Policy development, district budget, board reporting.", typical_promotion_path="→ Education Consultant"),
    ],
}


def _map_career_family(title_lower: str) -> str:
    """Map a job title to a career family key."""
    if any(w in title_lower for w in ["developer", "engineer", "software", "programmer", "tech lead", "principal"]):
        return "software"
    if any(w in title_lower for w in ["data", "analyst", "scientist", "analytics"]):
        return "data"
    if any(w in title_lower for w in ["security", "ciso", "soc", "analyst"]):
        return "security"
    if any(w in title_lower for w in ["manager", "director", "vp", "supervisor", "lead", "chief", "head"]):
        return "management"
    if any(w in title_lower for w in ["nurse", "nursing", "cna", "lpn", "rn", "medical", "clinical", "health"]):
        return "healthcare"
    if any(w in title_lower for w in ["teacher", "instructor", "professor", "education", "principal", "superintendent"]):
        return "education"
    return "software"  # default to most common


def career_path(entry_job: str, years: int) -> CareerPathResult:
    """Get realistic career progression with salary milestones.

    Maps the entry job to a career family, then returns the steps
    that fit within the given time horizon.
    """
    title_lower = entry_job.lower()
    family_key = _map_career_family(title_lower)

    all_steps = PROGRESSION_MAPS.get(family_key, PROGRESSION_MAPS["software"])

    # Filter steps that fit within the years horizon
    steps = [s for s in all_steps if s.years_to_reach <= years]
    if not steps:
        steps = [all_steps[0]]

    return CareerPathResult(
        entry_title=entry_job,
        years=years,
        steps=steps,
        data_source="database",
    )