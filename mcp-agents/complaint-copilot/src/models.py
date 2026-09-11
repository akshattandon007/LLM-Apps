"""Pydantic models for Complaint Copilot."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IssueType(str, Enum):
    """Supported complaint issue types."""

    DELAYED_CANCELLED_FLIGHT = "delayed_cancelled_flight"
    DEFECTIVE_PRODUCT = "defective_product"
    OVERCHARGE_BILLING_ERROR = "overcharge_billing_error"
    POOR_SERVICE = "poor_service"
    LANDLORD_TENANT = "landlord_tenant"
    WARRANTY_CLAIM = "warranty_claim"
    CONTRACT_DISPUTE = "contract_dispute"


class Country(str, Enum):
    """Supported countries for rights lookup."""

    US = "us"
    UK = "uk"
    EU = "eu"


class ComplaintRequest(BaseModel):
    """Input for drafting a complaint."""

    company: str = Field(..., description="Company or entity being complained about")
    issue: str = Field(..., description="Description of the issue")
    amount: Optional[str] = Field(None, description="Amount claimed (e.g. '$350' or 'repair cost')")
    outcome: Optional[str] = Field(None, description="Desired resolution")


class OmbudsmanRequest(BaseModel):
    """Input for finding the right ombudsman."""

    company: str = Field(..., description="Company name")
    issue_type: IssueType = Field(..., description="Type of issue")


class RightsRequest(BaseModel):
    """Input for looking up statutory rights."""

    issue_type: IssueType = Field(..., description="Type of issue")
    country: Country = Field(..., description="Country code")


class TrackRequest(BaseModel):
    """Input for tracking a complaint."""

    company: str = Field(..., description="Company name")
    reference: Optional[str] = Field(None, description="Complaint reference number")


class EscalateRequest(BaseModel):
    """Input for escalating to a regulator."""

    company: str = Field(..., description="Company name")
    ombudsman: str = Field(..., description="Ombudsman/regulator name")
    case_summary: str = Field(..., description="Summary of the case")


class ComplaintStatus(BaseModel):
    """Status of a tracked complaint."""

    reference: str
    company: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: list[str] = Field(default_factory=list)
    next_action: Optional[str] = None


class StatutoryRight(BaseModel):
    """Consumer statutory right information."""

    right: str
    summary: str
    deadline: str
    reference: str
    details: str


class OmbudsmanInfo(BaseModel):
    """Ombudsman or regulator information."""

    name: str
    url: str
    jurisdiction: str
    eligibility: str
    notes: Optional[str] = None
