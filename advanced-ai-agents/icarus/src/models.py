"""Pydantic models for Icarus: Alert, Incident, Evidence, RootCause, Remediation, PostMortem."""

from __future__ import annotations

import enum
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ──────────────────────────────────────────────────────────────────


class AlertSeverity(str, enum.Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


class AlertSource(str, enum.Enum):
    pagerduty = "pagerduty"
    prometheus = "prometheus"
    cloudwatch = "cloudwatch"
    manual = "manual"


class RemediationActionType(str, enum.Enum):
    rollback = "rollback"
    restart = "restart"
    scale_up = "scale_up"
    feature_flag = "feature_flag"
    other = "other"


class RemediationActionStatus(str, enum.Enum):
    proposed = "proposed"
    approved = "approved"
    executed = "executed"
    skipped = "skipped"


# ── Core data models ───────────────────────────────────────────────────────


class Alert(BaseModel):
    id: str
    source: AlertSource
    severity: AlertSeverity
    title: str
    message: str
    service: str
    timestamp: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    id: str
    alert: Alert
    severity: AlertSeverity
    status: str = "open"  # open | mitigated | resolved
    opened_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None


class LogEntry(BaseModel):
    timestamp: datetime
    service: str
    level: str
    message: str
    source: str = "observability"


class Metric(BaseModel):
    name: str
    service: str
    timestamp: datetime
    value: float
    unit: str = ""
    labels: dict[str, str] = Field(default_factory=dict)


class Deployment(BaseModel):
    sha: str
    service: str
    timestamp: datetime
    author: str
    status: str = "deployed"  # deployed | rolled_back | failed
    version: str = ""


# ── Triage / Evidence ──────────────────────────────────────────────────────


class Evidence(BaseModel):
    alert: Alert
    logs: list[LogEntry] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    deployments: list[Deployment] = Field(default_factory=list)


# ── RCA ────────────────────────────────────────────────────────────────────


class Correlation(BaseModel):
    kind: str
    description: str
    confidence: float
    evidence_refs: list[str] = Field(default_factory=list)


class RootCause(BaseModel):
    incident_id: str
    summary: str
    hypothesis: str
    confidence: float
    correlations: list[Correlation] = Field(default_factory=list)
    related_incidents: list[str] = Field(default_factory=list)
    reasoning_steps: list[str] = Field(default_factory=list)


# ── Remediation ────────────────────────────────────────────────────────────


class RemediationAction(BaseModel):
    id: str
    type: RemediationActionType
    description: str
    command: str
    destructive: bool = False
    status: RemediationActionStatus = RemediationActionStatus.proposed
    rationale: str = ""
    approved_at: datetime | None = None
    executed_at: datetime | None = None


class RemediationPlan(BaseModel):
    incident_id: str
    actions: list[RemediationAction] = Field(default_factory=list)
    approved: bool = False


# ── Post-Mortem ────────────────────────────────────────────────────────────


class TimelineEntry(BaseModel):
    timestamp: datetime
    event: str
    detail: str = ""


class ActionItem(BaseModel):
    title: str
    owner: str = "platform"
    priority: str = "medium"
    status: str = "open"


class PostMortem(BaseModel):
    incident_id: str
    title: str
    summary: str
    severity: AlertSeverity
    timeline: list[TimelineEntry] = Field(default_factory=list)
    impact: str = ""
    root_cause: RootCause | None = None
    action_items: list[ActionItem] = Field(default_factory=list)
    remediation: RemediationPlan | None = None
    generated_at: datetime = Field(default_factory=utcnow)