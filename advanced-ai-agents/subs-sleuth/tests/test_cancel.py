"""Tests for the Cancellation Agent."""

from subs_sleuth.models import Subscription, CancellationGuide
from subs_sleuth.cancel_agent import research_cancellation, _known_cancellation


class TestCancelAgent:
    def test_known_cancellation_netflix(self):
        result = _known_cancellation("Netflix")
        assert result is not None
        assert result.merchant == "Netflix"
        assert result.cancellation_method == "website"
        assert len(result.steps) > 0
        assert "netflix.com" in result.url

    def test_known_cancellation_spotify(self):
        result = _known_cancellation("Spotify Premium")
        assert result is not None
        assert "spotify.com/account" in result.url

    def test_known_cancellation_unknown(self):
        result = _known_cancellation("SomeRandomService")
        assert result is None

    def test_known_cancellation_chatgpt(self):
        result = _known_cancellation("ChatGPT Plus")
        assert result is not None
        assert "chat.openai.com" in result.url
        assert result.difficulty == "easy"

    def test_research_cancellation_with_known_merchant(self):
        sub = Subscription(merchant="Netflix", amount=15.99)
        guide = research_cancellation(sub)
        assert guide.merchant == "Netflix"
        assert len(guide.steps) > 0
        # Should match known database
        assert "netflix.com" in guide.url

    def test_research_cancellation_falls_back_to_search(self):
        """For an unknown merchant, it falls back to web search/generic steps."""
        sub = Subscription(merchant="MysteryBox Monthly")
        guide = research_cancellation(sub)
        assert guide.merchant == "MysteryBox Monthly"
        # Should at least have steps from the fallback
        assert len(guide.steps) > 0

    def test_known_cancellation_disney(self):
        result = _known_cancellation("Disney+")
        assert result is not None
        assert "disneyplus.com" in result.url

    def test_known_cancellation_guide_structure(self):
        result = _known_cancellation("Netflix")
        assert isinstance(result, CancellationGuide)
        assert hasattr(result, "cancellation_method")
        assert hasattr(result, "difficulty")
        assert hasattr(result, "source")
        assert result.source == "known_database"