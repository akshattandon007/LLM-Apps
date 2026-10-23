"""
triallight — Plain-language clinical trial assistant.

RAG pipeline: search ClinicalTrials.gov → retrieve full study records
→ LLM-augment into plain-language eligibility & summary.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class StudyStatus(str, enum.Enum):
    RECRUITING = "RECRUITING"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    SUSPENDED = "SUSPENDED"
    WITHDRAWN = "WITHDRAWN"
    UNKNOWN = "UNKNOWN"


@dataclass
class Location:
    city: str
    state: str
    country: str
    zip: str = ""


@dataclass
class Condition:
    name: str
    description: str = ""


@dataclass
class EligibilityCriterion:
    category: str  # "INCLUSION" or "EXCLUSION"
    text: str


@dataclass
class StudyProtocol:
    nct_id: str
    brief_title: str
    official_title: str = ""
    status: StudyStatus = StudyStatus.UNKNOWN
    conditions: list[str] = field(default_factory=list)
    locations: list[Location] = field(default_factory=list)
    brief_summary: str = ""
    detailed_description: str = ""
    eligibility_criteria: list[EligibilityCriterion] = field(default_factory=list)
    enrollment_count: int = 0
    phase: str = ""
    start_date: str = ""
    completion_date: str = ""
    lead_sponsor: str = ""
    url: str = ""


@dataclass
class PubMedArticle:
    pmid: str
    title: str
    authors: str = ""
    journal: str = ""
    year: str = ""
    abstract: str = ""
    url: str = ""


@dataclass
class SearchResult:
    query: str
    location: Optional[str]
    studies: list[StudyProtocol]
    recent_articles: list[PubMedArticle] = field(default_factory=list)