"""Streak tracking, badge system, and point scoring."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from .models import Badge, UserProfile


_client = None


def set_client(client):
    """Replace the scoring backend for testing."""
    global _client
    _client = client


# -- Badge definitions --
BADGE_TIERS = [
    Badge(
        id="first_save",
        name="First Save",
        description="Save your first item from going to waste",
        icon="🌱",
    ),
    Badge(
        id="day_3",
        name="Weekend Warrior",
        description="Maintain a 3-day zero-waste streak",
        icon="🔥",
    ),
    Badge(
        id="day_7",
        name="Week Zero",
        description="7-day zero-waste streak — one full week!",
        icon="⭐",
    ),
    Badge(
        id="day_14",
        name="Fortnight Fortress",
        description="14-day zero-waste streak",
        icon="🛡️",
    ),
    Badge(
        id="day_30",
        name="Zero Waste Hero",
        description="30-day zero-waste streak — one month!",
        icon="🏆",
    ),
    Badge(
        id="day_60",
        name="Waste Warrior",
        description="60-day zero-waste streak — two months strong",
        icon="💪",
    ),
    Badge(
        id="day_100",
        name="Centurion of Zero Waste",
        description="100-day zero-waste streak — legendary!",
        icon="👑",
    ),
    Badge(
        id="items_10",
        name="Dozer",
        description="Save 10 items total from going to waste",
        icon="📦",
    ),
    Badge(
        id="items_50",
        name="Food Guardian",
        description="Save 50 items total from going to waste",
        icon="🗡️",
    ),
    Badge(
        id="items_100",
        name="Trash Slayer",
        description="Save 100 items from the bin — incredible!",
        icon="🐉",
    ),
    Badge(
        id="points_500",
        name="Point Collector",
        description="Accumulate 500 points",
        icon="💰",
    ),
    Badge(
        id="points_2000",
        name="Point Millionaire (almost)",
        description="Accumulate 2,000 points",
        icon="💎",
    ),
    Badge(
        id="challenges_5",
        name="Challenge Accepted",
        description="Complete 5 challenges",
        icon="🎯",
    ),
    Badge(
        id="challenges_20",
        name="Challenge Master",
        description="Complete 20 challenges",
        icon="🏅",
    ),
]


def _get_streak_badges(streak: int) -> list[Badge]:
    """Return badges earned at the current streak length."""
    earned = []
    for badge in BADGE_TIERS:
        if badge.id.startswith("day_"):
            days = int(badge.id.split("_")[1])
            if streak >= days:
                earned.append(badge)
    return earned


def _get_milestone_badges(
    profile: UserProfile,
) -> list[Badge]:
    """Check which milestone badges are newly earned."""
    earned = []
    for badge in BADGE_TIERS:
        already_has = any(b.id == badge.id for b in profile.badges)
        if already_has:
            continue

        if badge.id == "first_save" and profile.total_items_saved >= 1:
            earned.append(badge)
        elif badge.id == "items_10" and profile.total_items_saved >= 10:
            earned.append(badge)
        elif badge.id == "items_50" and profile.total_items_saved >= 50:
            earned.append(badge)
        elif badge.id == "items_100" and profile.total_items_saved >= 100:
            earned.append(badge)
        elif badge.id == "points_500" and profile.total_points >= 500:
            earned.append(badge)
        elif badge.id == "points_2000" and profile.total_points >= 2000:
            earned.append(badge)
        elif badge.id == "challenges_5" and profile.challenges_completed >= 5:
            earned.append(badge)
        elif badge.id == "challenges_20" and profile.challenges_completed >= 20:
            earned.append(badge)

    # Streak badges
    for sb in _get_streak_badges(profile.current_streak):
        if not any(b.id == sb.id for b in profile.badges):
            earned.append(sb)

    return earned


def update_streak(profile: UserProfile, today: Optional[date] = None) -> UserProfile:
    """Update the user's streak based on activity.

    Call this once per day when the user reports activity.
    Resets streak to 0 if a day was missed.

    Parameters
    ----------
    profile : UserProfile
        Current user profile.
    today : date or None
        Current date (defaults to today).

    Returns
    -------
    UserProfile with updated streak.
    """
    if _client is not None:
        return _client(mode="update_streak", profile=profile, today=today)

    today = today or date.today()

    if profile.last_active_date is None:
        # First activity ever
        profile.current_streak = 1
        profile.longest_streak = 1
    elif profile.last_active_date == today:
        # Already logged today — no change
        return profile
    elif profile.last_active_date == today - timedelta(days=1):
        # Consecutive day
        profile.current_streak += 1
        if profile.current_streak > profile.longest_streak:
            profile.longest_streak = profile.current_streak
    else:
        # Gap — streak broken
        profile.current_streak = 1

    profile.last_active_date = today
    return profile


def record_use(
    profile: UserProfile,
    items_saved: int = 1,
    points_earned: int = 10,
    challenge_bonus: int = 0,
    today: Optional[date] = None,
) -> tuple[UserProfile, list[Badge]]:
    """Record a user action (used an item, completed a challenge).

    Updates streak, points, items saved, and checks for new badges.

    Parameters
    ----------
    profile : UserProfile
    items_saved : int
        How many items were prevented from going to waste.
    points_earned : int
        Base points for the action.
    challenge_bonus : int
        Extra points from completing a challenge.
    today : date or None

    Returns
    -------
    (updated_profile, new_badges_earned)
    """
    if _client is not None:
        return _client(
            mode="record_use",
            profile=profile,
            items_saved=items_saved,
            points_earned=points_earned,
            challenge_bonus=challenge_bonus,
            today=today,
        )

    before_badges = set(b.id for b in profile.badges)

    # Update streak
    profile = update_streak(profile, today)

    # Accumulate stats
    profile.total_items_saved += items_saved
    profile.total_points += points_earned + challenge_bonus
    if challenge_bonus > 0:
        profile.challenges_completed += 1

    # Check for new badges
    new_badges = _get_milestone_badges(profile)
    today_dt = today or date.today()
    for badge in new_badges:
        if badge.id not in before_badges:
            badge.earned_date = today_dt
            profile.badges.append(badge)

    return profile, new_badges


def summarize(profile: UserProfile) -> str:
    """Return a human-readable summary of the user's stats."""
    lines = [
        f"🔥  Current streak: {profile.current_streak} day(s)",
        f"🏆  Longest streak: {profile.longest_streak} day(s)",
        f"📦  Items saved:    {profile.total_items_saved}",
        f"⭐  Points:          {profile.total_points}",
        f"🎯  Challenges done: {profile.challenges_completed}",
    ]
    if profile.badges:
        badge_line = " | ".join(
            f"{b.icon} {b.name}" for b in profile.badges
        )
        lines.append(f"\n🏅  Badges:\n   {badge_line}")

    return "\n".join(lines)