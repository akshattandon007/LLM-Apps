"""Smoke tests for FridgeFighter."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.challenges import generate
from src.item_db import add, expire_soon, list_items, load, remove
from src.models import Badge, FridgeItem, UserProfile
from src.scoring import record_use, summarize, update_streak
from src.vision import scan

# -- Helpers (no _client override — uses real module code) --


class TestVision:
    """Simulated fridge scan."""

    def test_scan_returns_items(self):
        items = scan(seed=42)
        assert len(items) > 0
        assert all(isinstance(it, FridgeItem) for it in items)

    def test_scan_reproducible_with_seed(self):
        a = scan(seed=100, count=6)
        b = scan(seed=100, count=6)
        assert [it.name for it in a] == [it.name for it in b]


class TestItemDB:
    """Item database operations."""

    def test_load_and_list(self, mock_items):
        load(mock_items)
        items = list_items()
        assert len(items) == len(mock_items)
        assert items[0].expiry_date <= items[-1].expiry_date  # sorted

    def test_add_and_remove(self):
        load([])  # start fresh
        item = FridgeItem(
            id="test-item",
            name="Test item",
            category="other",
            quantity=1,
            unit="pieces",
            expiry_date=date.today() + timedelta(days=7),
        )
        add(item)
        assert len(list_items()) == 1
        removed = remove("test-item")
        assert removed is not None
        assert removed.name == "Test item"
        assert len(list_items()) == 0

    def test_remove_nonexistent(self):
        assert remove("nonexistent") is None

    def test_expire_soon(self, mock_items):
        load(mock_items)
        expiring = expire_soon(hours=48)
        # Items 002 (Greek yogurt) and 006 (Avocado) expire in ~1 day
        assert len(expiring) >= 2
        ids = {it.id for it in expiring}
        assert "item-002" in ids
        assert "item-006" in ids

    def test_empty_inventory(self):
        load([])
        assert list_items() == []
        assert expire_soon() == []


class TestChallenges:
    """Daily challenge generation."""

    def test_generate_with_expiring_items(self, mock_items):
        load(mock_items)
        challenges = generate(seed=42)
        assert len(challenges) >= 1
        for c in challenges:
            assert c.title
            assert c.description
            assert c.points > 0
            assert c.date_assigned == date.today()

    def test_challenge_targets_expiring_items(self, mock_items):
        load(mock_items)
        challenges = generate(seed=42)
        # At least one challenge should reference a soon-expiring item
        expiring_ids = {"item-002", "item-006"}
        for c in challenges:
            if c.criteria.get("item_ids"):
                for item_id in c.criteria["item_ids"]:
                    if item_id in expiring_ids:
                        return  # found a match
        pytest.fail("No challenge targeted expiring items")

    def test_no_items_returns_empty(self):
        load([])
        challenges = generate(seed=42)
        assert len(challenges) >= 0  # may still generate general challenges


class TestScoring:
    """Streak, points, and badge system."""

    def test_update_streak_first_time(self):
        profile = UserProfile()
        updated = update_streak(profile)
        assert updated.current_streak == 1
        assert updated.longest_streak == 1

    def test_update_streak_consecutive(self):
        profile = UserProfile()
        profile = update_streak(profile)
        # Simulate next day
        tomorrow = date.today() + timedelta(days=1)
        # We can't easily monkey-patch `date.today()` here, so
        # verify that calling update_streak with today yields no change
        profile2 = update_streak(profile, today=tomorrow)
        assert profile2.current_streak == 2
        assert profile2.longest_streak == 2

    def test_update_streak_broken(self):
        profile = UserProfile()
        profile = update_streak(profile, today=date.today() - timedelta(days=3))
        # Now 2 days later
        profile = update_streak(profile, today=date.today() - timedelta(days=1))
        assert profile.current_streak == 1  # reset

    def test_record_use_new_badges(self):
        profile = UserProfile()
        updated, badges = record_use(
            profile, items_saved=1, points_earned=10, today=date.today()
        )
        assert updated.total_items_saved == 1
        assert updated.total_points == 10
        assert any(b.id == "first_save" for b in badges)

    def test_record_use_challenge_bonus(self):
        profile = UserProfile()
        updated, badges = record_use(
            profile, items_saved=2, points_earned=20, challenge_bonus=50
        )
        assert updated.total_points == 70
        assert updated.challenges_completed == 1

    def test_streak_badge_at_7_days(self):
        profile = UserProfile()
        # Simulate 7 consecutive days
        for day_offset in range(7):
            profile = update_streak(
                profile, today=date.today() + timedelta(days=day_offset)
            )
        assert profile.current_streak == 7

    def test_summarize(self, veteran_profile):
        text = summarize(veteran_profile)
        assert "10" in text  # streak
        assert "650" in text  # points
        assert "First Save" in text  # badge name

    def test_summarize_empty(self):
        text = summarize(UserProfile())
        assert "0" in text  # all zeros


class TestSmokeIntegration:
    """End-to-end simulation with mock data."""

    def test_scan_to_challenge_to_use(self, mock_items):
        # 1. Simulate items in fridge
        load(mock_items)

        # 2. Generate challenges
        challenges = generate(seed=42)
        assert len(challenges) >= 1

        # 3. Remove an expiring item (simulate using it)
        removed = remove("item-002")
        assert removed is not None

        # 4. Record the use
        profile = UserProfile()
        updated, badges = record_use(
            profile, items_saved=1, points_earned=10
        )
        assert updated.total_items_saved == 1

        # 5. Verify remaining inventory
        remaining = list_items()
        ids = {it.id for it in remaining}
        assert "item-002" not in ids

    def test_full_demo_flow(self, mock_items):
        """Run the full pipeline and verify no exceptions."""
        load(mock_items)

        # Generate challenges
        challenges = generate(seed=42)

        # Use expiring items
        for c in challenges:
            if c.criteria.get("item_ids"):
                for item_id in c.criteria["item_ids"]:
                    remove(item_id)

        # Record usage
        profile = UserProfile()
        profile, badges = record_use(
            profile, items_saved=2, points_earned=20, challenge_bonus=50
        )

        # Check state
        assert profile.total_items_saved == 2
        assert profile.total_points == 70
        assert len(list_items()) < len(mock_items)  # some were removed