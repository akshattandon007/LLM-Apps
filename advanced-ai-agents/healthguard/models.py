"""Shared data models for HealthGuard multi-agent system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class Urgency(str, Enum):
    ROUTINE = "routine"
    SOON = "soon"
    URGENT = "urgent"
    EMERGENCY = "emergency"


@dataclass
class DrugInfo:
    """Information about a single drug."""
    name: str
    rxcui: Optional[str] = None
    generic_name: Optional[str] = None
    brand_names: list[str] = field(default_factory=list)
    drug_class: Optional[str] = None
    source: str = "live"


@dataclass
class InteractionResult:
    """Result of a pairwise drug interaction check."""
    drug_a: str
    drug_b: str
    severity: Severity = Severity.LOW
    description: str = ""
    management: str = ""
    interaction_found: bool = False
    source: str = "live"


@dataclass
class SymptomAssessment:
    """Assessment of a reported symptom."""
    symptom: str
    possible_conditions: list[str] = field(default_factory=list)
    urgency: Urgency = Urgency.ROUTINE
    recommendations: list[str] = field(default_factory=list)
    requires_immediate_care: bool = False
    source: str = "live"


@dataclass
class ConditionInfo:
    """Information about a medical condition."""
    name: str
    description: str = ""
    symptoms: list[str] = field(default_factory=list)
    treatments: list[str] = field(default_factory=list)
    when_to_see_doctor: str = ""
    prevention_tips: list[str] = field(default_factory=list)
    source: str = "live"


@dataclass
class HealthReport:
    """Final compiled health report combining all agent findings."""
    drug_interactions: list[InteractionResult] = field(default_factory=list)
    symptom_assessments: list[SymptomAssessment] = field(default_factory=list)
    condition_info: list[ConditionInfo] = field(default_factory=list)
    summary: str = ""
    key_warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    generated_at: str = ""
    source: str = "live"