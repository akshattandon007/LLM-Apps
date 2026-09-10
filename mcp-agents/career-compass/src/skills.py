"""Skills gap analysis between current and target roles.

Identifies missing certifications, tools, and skills needed to transition
from one occupation to another, with estimated costs and typical courses.
"""

from __future__ import annotations

import re

from .databases import find_occupation_by_title, get_all_occupations
from .models import SkillGap, SkillsGapResult, DegreeLevel

# ── Skill maps for common role transitions ─────────────────────────────────────
# Each entry maps (current_title_pattern, target_title_pattern) -> gaps

SKILL_MAPS: list[tuple[str, str, list[SkillGap]]] = [
    # Support -> Developer
    (
        "support",
        "developer",
        [
            SkillGap(skill_name="Programming Language (Python/Java/JS)", category="tool", importance="required", typical_courses=["CS 101", "Codecademy Pro"], typical_cost_range="$0 - $500"),
            SkillGap(skill_name="Version Control (Git)", category="tool", importance="required", typical_courses=["Git for Professionals"], typical_cost_range="$0 - $50"),
            SkillGap(skill_name="Data Structures & Algorithms", category="certification", importance="required", typical_courses=["LeetCode", "Algorithms Specialization (Coursera)"], typical_cost_range="$0 - $400"),
            SkillGap(skill_name="Cloud Platform (AWS/Azure/GCP)", category="tool", importance="recommended", typical_courses=["AWS Developer Associate", "Google Cloud Engineer"], typical_cost_range="$100 - $300"),
            SkillGap(skill_name="System Design", category="tool", importance="recommended", typical_courses=["Designing Data-Intensive Applications", "System Design Interview"], typical_cost_range="$30 - $100"),
        ],
    ),
    # Admin -> Developer
    (
        "administrator",
        "developer",
        [
            SkillGap(skill_name="Programming (Multi-paradigm)", category="tool", importance="required", typical_courses=["Full-Stack Bootcamp", "Python for Everybody"], typical_cost_range="$0 - $15,000"),
            SkillGap(skill_name="Software Development Lifecycle", category="certification", importance="required", typical_courses=["Agile Fundamentals", "Scrum Master"], typical_cost_range="$100 - $1,500"),
            SkillGap(skill_name="CI/CD Pipelines", category="tool", importance="recommended", typical_courses=["Jenkins Administration", "GitHub Actions"], typical_cost_range="$0 - $200"),
        ],
    ),
    # Accountant -> Analyst
    (
        "accountant",
        "analyst",
        [
            SkillGap(skill_name="Data Analysis (SQL/Python)", category="tool", importance="required", typical_courses=["SQL for Data Analysis", "DataCamp Data Analyst"], typical_cost_range="$0 - $300"),
            SkillGap(skill_name="Data Visualization (Tableau/Power BI)", category="tool", importance="required", typical_courses=["Tableau Fundamentals", "Data Visualization with Python"], typical_cost_range="$0 - $300"),
            SkillGap(skill_name="Statistical Analysis", category="certification", importance="recommended", typical_courses=["Coursera Statistics", "Khan Academy"], typical_cost_range="$0 - $100"),
            SkillGap(skill_name="Machine Learning Basics", category="tool", importance="nice_to_have", typical_courses=["Andrew Ng ML Course", "Fast.ai"], typical_cost_range="$0 - $100"),
        ],
    ),
    # Teacher -> Instructional Design
    (
        "teacher",
        "instructional",
        [
            SkillGap(skill_name="Instructional Design Models", category="certification", importance="required", typical_courses=["ATD Instructional Design Certificate", "Coursera Instructional Design"], typical_cost_range="$500 - $2,000"),
            SkillGap(skill_name="Authoring Tools (Articulate/Captivate)", category="tool", importance="required", typical_courses=["Articulate 360 Masterclass"], typical_cost_range="$200 - $1,000"),
            SkillGap(skill_name="LMS Administration", category="tool", importance="recommended", typical_courses=["Moodle Administration", "Canvas LMS"], typical_cost_range="$0 - $500"),
            SkillGap(skill_name="UX for Learning", category="tool", importance="nice_to_have", typical_courses=["Interaction Design Foundation"], typical_cost_range="$0 - $200"),
        ],
    ),
    # Nurse -> Healthcare Admin
    (
        "nurse",
        "administrator",
        [
            SkillGap(skill_name="Healthcare Management", category="certification", importance="required", typical_courses=["MHA Degree", "ACHE Certification"], typical_cost_range="$20,000 - $80,000"),
            SkillGap(skill_name="Health Informatics", category="tool", importance="required", typical_courses=["Health IT Specialization", "Epic Systems Training"], typical_cost_range="$500 - $5,000"),
            SkillGap(skill_name="Healthcare Law & Regulations", category="certification", importance="required", typical_courses=["Healthcare Compliance Certificate"], typical_cost_range="$500 - $2,000"),
            SkillGap(skill_name="Budgeting & Operations", category="tool", importance="recommended", typical_courses=["Financial Management for Healthcare"], typical_cost_range="$200 - $1,000"),
        ],
    ),
    # General developer -> data scientist
    (
        "developer",
        "scientist",
        [
            SkillGap(skill_name="Advanced Statistics & Probability", category="certification", importance="required", typical_courses=["Stats for Data Science", "HarvardX Data Science"], typical_cost_range="$0 - $500"),
            SkillGap(skill_name="Machine Learning Engineering", category="tool", importance="required", typical_courses=["ML Engineering for Production (DeepLearning.AI)", "CS229"], typical_cost_range="$0 - $500"),
            SkillGap(skill_name="Experimental Design & A/B Testing", category="certification", importance="required", typical_courses=["Coursera A/B Testing", "Udacity A/B Testing"], typical_cost_range="$0 - $400"),
            SkillGap(skill_name="Deep Learning Frameworks", category="tool", importance="recommended", typical_courses=["Fast.ai", "PyTorch Tutorials"], typical_cost_range="$0 - $200"),
            SkillGap(skill_name="Data Engineering (Spark, dbt)", category="tool", importance="nice_to_have", typical_courses=["Spark Fundamentals", "dbt Fundamentals"], typical_cost_range="$0 - $200"),
        ],
    ),
    # Analyst -> data scientist
    (
        "analyst",
        "scientist",
        [
            SkillGap(skill_name="Machine Learning Algorithms", category="tool", importance="required", typical_courses=["ML by Andrew Ng", "Scikit-Learn Course"], typical_cost_range="$0 - $300"),
            SkillGap(skill_name="Deep Learning", category="tool", importance="recommended", typical_courses=["Deep Learning Specialization (DeepLearning.AI)"], typical_cost_range="$0 - $400"),
            SkillGap(skill_name="Python for Data Science (Advanced)", category="tool", importance="required", typical_courses=["Python Data Science Handbook", "DataCamp Advanced Python"], typical_cost_range="$0 - $300"),
            SkillGap(skill_name="MLOps & Model Deployment", category="tool", importance="nice_to_have", typical_courses=["MLOps Specialization", "Kubeflow"], typical_cost_range="$100 - $500"),
        ],
    ),
    # General -> any transition
    (
        "",
        "",
        [
            SkillGap(skill_name="LinkedIn Profile Optimization", category="tool", importance="required", typical_courses=["LinkedIn Learning Career Optimization"], typical_cost_range="$0 - $50"),
            SkillGap(skill_name="Portfolio Building", category="tool", importance="recommended", typical_courses=["Create a Career Portfolio"], typical_cost_range="$0"),
            SkillGap(skill_name="Industry Certifications Research", category="certification", importance="recommended", typical_courses=["BLS Career Outlook Guides"], typical_cost_range="$0"),
        ],
    ),
]


def _generate_generic_gaps(current: str, target: str, current_occ_edu: DegreeLevel, target_occ_edu: DegreeLevel) -> list[SkillGap]:
    """Generate generic gaps when no specific skill map exists."""
    gaps: list[SkillGap] = []

    # Education gap
    edu_order = {DegreeLevel.NONE: 0, DegreeLevel.HIGH_SCHOOL: 1, DegreeLevel.ASSOCIATES: 2, DegreeLevel.BACHELORS: 3, DegreeLevel.MASTERS: 4, DegreeLevel.DOCTORAL: 5}
    current_level = edu_order.get(current_occ_edu, 0)
    target_level = edu_order.get(target_occ_edu, 0)

    if target_level > current_level:
        edu_names = {1: "High School / GED", 2: "Associate's Degree", 3: "Bachelor's Degree", 4: "Master's Degree", 5: "Doctoral Degree"}
        gaps.append(
            SkillGap(
                skill_name=f"Education: {edu_names.get(target_level, 'Degree')}",
                category="certification",
                importance="required",
                typical_courses=[f"Enroll in {edu_names.get(target_level, 'Degree')} program"],
                typical_cost_range="$5,000 - $50,000",
            )
        )

    # Generic industry transition gaps
    gaps.append(
        SkillGap(
            skill_name=f"Industry Knowledge: {target} domain",
            category="tool",
            importance="required",
            typical_courses=["Industry-specific certifications", "Domain research via O*NET"],
            typical_cost_range="$0 - $500",
        )
    )
    gaps.append(
        SkillGap(
            skill_name="Resume & Interview Prep for career switch",
            category="tool",
            importance="recommended",
            typical_courses=["Career transition workshops", "Informational interviews"],
            typical_cost_range="$0 - $200",
        )
    )
    return gaps


def skills_gap(current_title: str, target_title: str) -> SkillsGapResult:
    """Identify certifications and courses needed to move from current to target.

    Uses predefined skill maps for common transitions and generates
    education-based gap analysis for less common ones.
    """
    current_lower = current_title.lower()
    target_lower = target_title.lower()

    current_occ = find_occupation_by_title(current_title)
    target_occ = find_occupation_by_title(target_title)

    current_edu = current_occ.typical_education if current_occ else DegreeLevel.NONE
    target_edu = target_occ.typical_education if target_occ else DegreeLevel.BACHELORS

    # Try explicit skill map matches first
    gaps: list[SkillGap] = []
    for cur_pat, tar_pat, skill_list in SKILL_MAPS:
        cur_match = cur_pat in current_lower if cur_pat else True
        tar_match = tar_pat in target_lower if tar_pat else True
        if cur_match and tar_match:
            gaps.extend(skill_list)
            break

    # If no specific map matched, generate generic ones
    if not gaps:
        gaps = _generate_generic_gaps(current_title, target_title, current_edu, target_edu)

    return SkillsGapResult(
        current_title=current_title,
        target_title=target_title,
        gaps=gaps,
        data_source="database",
    )