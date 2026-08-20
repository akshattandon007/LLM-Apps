"""Pydantic models for FridgeFighter."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class FridgeItem(BaseModel):
    """An item detected in the fridge."""

    id: str = Field(description="Unique identifier")
    name: str = Field(description="Item name, e.g. 'Greek yogurt'")
    category: str = Field(
        description="Category: dairy, produce, meat, condiment, beverage, frozen, pantry, other"
    )
    quantity: int = Field(default=1, ge=1, description="Number of units")
    unit: str = Field(default="pieces", description="Unit type: pieces, ml, g, oz, lbs, etc.")
    expiry_date: date = Field(description="Estimated expiry date")
    confidence: float = Field(
        default=0.85, ge=0.0, le=1.0, description="AI detection confidence"
    )
    added_date: date = Field(default_factory=date.today, description="When the item was added")


class Challenge(BaseModel):
    """A daily challenge to use expiring items."""

    id: str = Field(description="Unique challenge identifier")
    title: str = Field(description="Short challenge title")
    description: str = Field(description="Detailed challenge description")
    criteria: dict = Field(
        default_factory=dict,
        description="Criteria dict: keys like item_ids, action, count, combine",
    )
    points: int = Field(default=50, ge=0, description="Points awarded on completion")
    completed: bool = Field(default=False)
    date_assigned: date = Field(default_factory=date.today)


class Badge(BaseModel):
    """A badge earned by the user."""

    id: str = Field(description="Badge identifier, e.g. 'first_save'")
    name: str = Field(description="Display name, e.g. 'First Save'")
    description: str = Field(description="How to earn this badge")
    icon: str = Field(default="🏅", description="Emoji icon")
    earned_date: Optional[date] = Field(default=None, description="When the user earned this")


class UserProfile(BaseModel):
    """Persistent user state."""

    current_streak: int = Field(default=0, ge=0, description="Consecutive days with at least one action")
    longest_streak: int = Field(default=0, ge=0, description="All-time longest streak")
    total_points: int = Field(default=0, ge=0, description="Accumulated points")
    total_items_saved: int = Field(default=0, ge=0, description="Items used before expiry")
    challenges_completed: int = Field(default=0, ge=0, description="Challenges fully completed")
    badges: list[Badge] = Field(default_factory=list)
    last_active_date: Optional[date] = Field(
        default=None, description="Last date the user logged activity"
    )


class ChallengeResult(BaseModel):
    """Result of running a challenge check."""

    challenge: Challenge
    item_names: list[str] = Field(default_factory=list)
    earned_points: int = 0
    new_badges: list[Badge] = Field(default_factory=list)
    streak_updated: bool = False


class ScanResult(BaseModel):
    """Result of a fridge scan."""

    items: list[FridgeItem] = Field(default_factory=list)
    total_items: int = 0
    expiring_soon: list[FridgeItem] = Field(default_factory=list)
    scan_date: datetime = Field(default_factory=datetime.now)