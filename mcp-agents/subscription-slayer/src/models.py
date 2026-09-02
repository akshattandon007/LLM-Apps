"""Pydantic models for Subscription Slayer."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Charge(BaseModel):
    """A single transaction from a bank statement or CSV."""

    transaction_date: date = Field(..., alias="date", description="Date of the transaction")
    description: str = Field(..., description="Transaction description / merchant name")
    amount: float = Field(..., gt=-1e6, lt=1e6, description="Transaction amount in dollars")
    merchant: Optional[str] = Field(None, description="Normalized merchant name")

    model_config = {"populate_by_name": True}


class Frequency(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKLY = "weekly"
    QUARTERLY = "quarterly"
    UNKNOWN = "unknown"


class Subscription(BaseModel):
    """A detected recurring subscription."""

    merchant: str = Field(..., description="Merchant / service name")
    amount: float = Field(..., gt=0, description="Charge amount per billing cycle")
    frequency: Frequency = Field(default=Frequency.UNKNOWN, description="Billing frequency")
    first_seen: Optional[date] = Field(None, description="First occurrence date")
    last_seen: date = Field(default_factory=date.today, description="Most recent occurrence date")
    occurrences: int = Field(default=1, ge=1, description="Number of occurrences detected")


class Category(str, Enum):
    STREAMING = "streaming"
    CLOUD = "cloud_storage"
    FITNESS = "fitness_wellness"
    NEWS = "news_media"
    SOFTWARE = "software_tools"
    PRODUCTIVITY = "productivity"
    MUSIC = "music"
    GAMING = "gaming"
    EDUCATION = "education"
    OTHER = "other"


class CategorizedSub(BaseModel):
    """A subscription enriched with a category and annual cost estimate."""

    merchant: str
    amount: float
    frequency: Frequency = Frequency.UNKNOWN
    category: Category = Field(default=Category.OTHER)
    annual_cost: float = Field(default=0.0, description="Estimated annual cost in dollars")
    is_trial: bool = Field(default=False, description="Currently in free trial period")
    trial_end: Optional[date] = Field(None, description="Trial conversion date, if known")
    first_seen: Optional[date] = None
    last_seen: date = Field(default_factory=date.today, description="Most recent occurrence date")
    occurrences: int = 1


class ScanResult(BaseModel):
    """Result of scanning a bank statement."""

    total_transactions: int = 0
    charges: list[Charge] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)