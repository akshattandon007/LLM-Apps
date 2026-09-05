"""Pydantic models for HomeFix MCP Server."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ServiceType(str, Enum):
    """Supported home service categories."""

    plumber = "plumber"
    electrician = "electrician"
    hvac = "hvac"
    handyman = "handyman"
    locksmith = "locksmith"
    general_contractor = "general_contractor"


class Pro(BaseModel):
    """A home service professional."""

    name: str = Field(description="Business or individual name")
    company: str = Field(description="Registered company name")
    service_types: list[ServiceType] = Field(description="Services offered")
    phone: str = Field(description="Contact phone number")
    zip_code: str = Field(description="Service area ZIP")
    rating: float = Field(ge=0.0, le=5.0, description="Average review rating")
    review_count: int = Field(ge=0, description="Number of reviews")
    years_in_business: int = Field(ge=0)
    licensed: bool = Field(default=False, description="License verified")
    insured: bool = Field(default=False, description="Insurance verified")
    bonded: bool = Field(default=False, description="Bond verified")
    available_now: bool = Field(default=False, description="Available for emergency dispatch")
    price_estimate: Optional[str] = Field(default=None, description="Estimated price range")


class Quote(BaseModel):
    """A price quote from a matched provider."""

    pro_name: str = Field(description="Professional name")
    company: str = Field(description="Company name")
    service_type: ServiceType
    estimated_price: str = Field(description="Price range or flat estimate")
    estimated_duration: str = Field(description="Expected job duration")
    available_date: Optional[str] = Field(default=None, description="Next available date")
    notes: str = Field(default="", description="Quote details or disclaimers")


class Appointment(BaseModel):
    """A booked appointment."""

    pro_name: str
    company: str
    service_type: ServiceType
    appointment_date: str
    appointment_time: str
    status: str = Field(default="confirmed", description="Booking status")
    confirmation_number: str = Field(default="", description="Booking confirmation ID")


class ServiceDefinition(BaseModel):
    """Definition of a service type with metadata."""

    service_type: ServiceType
    display_name: str
    common_issues: list[str]
    typical_price_range: str
    urgent: bool = Field(default=False, description="Is this typically an emergency service?")
    requires_license_check: bool = Field(default=True)