"""Financial data models — all agents communicate via these dataclasses."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import json


class IncomeType(Enum):
    SALARY = "salary"
    FREELANCE = "freelance"
    PASSIVE = "passive"
    BUSINESS = "business"
    OTHER = "other"


class ExpenseCategory(Enum):
    HOUSING = "housing"
    FOOD = "food"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    DEBT = "debt"
    SAVINGS = "savings"
    OTHER = "other"


class GoalType(Enum):
    EMERGENCY_FUND = "emergency_fund"
    HOUSE_DOWN_PAYMENT = "house_down_payment"
    RETIREMENT = "retirement"
    DEBT_FREEDOM = "debt_freedom"
    VACATION = "vacation"
    EDUCATION = "education"
    CAR = "car"
    CUSTOM = "custom"


@dataclass
class IncomeStream:
    name: str
    amount: float                     # annual gross
    income_type: IncomeType = IncomeType.OTHER
    growth_rate: float = 0.03         # annual growth assumption
    tax_rate: float = 0.22            # estimated effective tax rate

    @property
    def net_annual(self) -> float:
        return self.amount * (1 - self.tax_rate)

    @property
    def net_monthly(self) -> float:
        return self.net_annual / 12


@dataclass
class Expense:
    name: str
    amount: float                     # monthly
    category: ExpenseCategory = ExpenseCategory.OTHER
    essential: bool = True
    note: str = ""


@dataclass
class FinancialProfile:
    income_streams: list[IncomeStream] = field(default_factory=list)
    expenses: list[Expense] = field(default_factory=list)
    savings: float = 0.0
    monthly_surplus: float = 0.0
    debt: float = 0.0
    debt_interest: float = 0.0
    location: str = ""
    age: int = 30

    def total_income_net_monthly(self) -> float:
        return sum(s.net_monthly for s in self.income_streams)

    def total_expenses_monthly(self) -> float:
        return sum(e.amount for e in self.expenses)

    def compute_surplus(self) -> float:
        self.monthly_surplus = self.total_income_net_monthly() - self.total_expenses_monthly()
        return self.monthly_surplus

    def to_dict(self) -> dict:
        return {
            "income_streams": [
                {"name": s.name, "amount": s.amount, "type": s.income_type.value,
                 "net_monthly": round(s.net_monthly, 2)} for s in self.income_streams
            ],
            "expenses": [
                {"name": e.name, "amount": e.amount, "category": e.category.value,
                 "essential": e.essential} for e in self.expenses
            ],
            "savings": self.savings,
            "monthly_surplus": round(self.compute_surplus(), 2),
            "debt": self.debt,
            "debt_interest": self.debt_interest,
            "age": self.age,
        }


@dataclass
class Goal:
    name: str
    goal_type: GoalType = GoalType.CUSTOM
    target_amount: float = 0.0
    target_date_years: int = 5
    current_progress: float = 0.0
    priority: int = 3
    monthly_contribution: float = 0.0

    def amount_needed(self) -> float:
        return max(0.0, self.target_amount - self.current_progress)


@dataclass
class ScenarioResult:
    scenario_name: str
    projected_surplus_5y: float
    total_savings_5y: float
    goal_met: bool
    goal_progress_pct: float
    risk_level: str
    summary: str
    monthly_breakdown: list[dict] = field(default_factory=list)


class FinancialEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if isinstance(obj, dataclass):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        return super().default(obj)