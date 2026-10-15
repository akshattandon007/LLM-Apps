"""Shared data models for FairWheel agents."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class VehicleQuery:
    """The vehicle + buyer context every agent needs."""

    year: int
    make: str
    model: str
    budget: Optional[float] = None          # what the buyer is willing to pay
    annual_miles: int = 12_000              # miles driven per year
    fuel_price: float = 3.50                # $ per gallon
    family_size: int = 1                    # affects safety priority
    commute_miles: Optional[int] = None     # daily one-way commute (optional)


@dataclass
class SafetyReport:
    overall_rating: Optional[float] = None      # 0-5 stars
    front_rating: Optional[float] = None
    side_rating: Optional[float] = None
    vehicle_description: str = ""
    source: str = "live"                        # "live" or "simulated"
    error: str = ""


@dataclass
class RecallItem:
    campaign_number: str
    component: str
    summary: str
    consequence: str
    remedy: str


@dataclass
class RecallReport:
    recalls: list[RecallItem] = field(default_factory=list)
    source: str = "live"
    error: str = ""

    @property
    def count(self) -> int:
        return len(self.recalls)


@dataclass
class ComplaintCluster:
    component: str
    count: int
    sample: str = ""


@dataclass
class ComplaintReport:
    total_complaints: int = 0
    clusters: list[ComplaintCluster] = field(default_factory=list)
    source: str = "live"
    error: str = ""


@dataclass
class CostReport:
    combined_mpg: Optional[float] = None
    city_mpg: Optional[float] = None
    highway_mpg: Optional[float] = None
    annual_fuel_cost: Optional[float] = None
    five_year_fuel_cost: Optional[float] = None
    source: str = "live"
    error: str = ""

    def compute_fuel_costs(self, annual_miles: int, fuel_price: float) -> None:
        if not self.combined_mpg:
            return
        gallons_per_year = annual_miles / self.combined_mpg
        self.annual_fuel_cost = round(gallons_per_year * fuel_price, 2)
        self.five_year_fuel_cost = round(self.annual_fuel_cost * 5, 2)


@dataclass
class DealVerdict:
    verdict: str = "WAIT"                       # WORTH IT | WAIT | AVOID
    score: float = 0.0                          # 0-100 weighted score
    reasons: list[str] = field(default_factory=list)
    talking_points: list[str] = field(default_factory=list)
    scores_by_factor: dict = field(default_factory=dict)


@dataclass
class FairWheelReport:
    query: VehicleQuery
    safety: SafetyReport
    recalls: RecallReport
    complaints: ComplaintReport
    cost: CostReport
    verdict: DealVerdict

    def to_dict(self) -> dict:
        return asdict(self)