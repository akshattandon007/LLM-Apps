"""Fixtures for Parallel Lives smoke tests."""

from __future__ import annotations

from typing import Generator
from unittest.mock import MagicMock

import httpx
import pytest

from src.characters import get_character
from src.conversation import Conversation
from src.models import Character, CharacterVoice
from src.responder import set_client


# ---------------------------------------------------------------------------
# A simpler mock character — no LLM dependency, just test data.
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_einstein() -> Character:
    """A usable Einstein character for tests."""
    return Character(
        name="Albert Einstein",
        emoji="🧑‍🔬",
        period="1930s",
        personality="Playful, curious, slightly distracted.",
        greeting="Ah, a curious mind! Pull up a chair.",
        catchphrase="The important thing is not to stop questioning.",
    )


@pytest.fixture
def mock_cleopatra() -> Character:
    return Character(
        name="Cleopatra VII",
        emoji="👑",
        period="40 BC",
        personality="Regal, sharp-witted, strategic.",
        greeting="So. You have summoned the Queen of the Nile.",
        catchphrase="A queen does not ask. She commands.",
    )


@pytest.fixture
def conversation(mock_einstein: Character) -> Conversation:
    """A fresh conversation with Einstein."""
    return Conversation(mock_einstein)


# ---------------------------------------------------------------------------
# Mock httpx client — routes on URL pattern so fake responses work.
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_httpx_client() -> Generator[MagicMock, None, None]:
    """Fixture that injects a fake httpx client into responder."""

    def _fake_post(url, **kwargs):
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "*strokes beard thoughtfully* An intriguing question from across the centuries."}}]
        }
        return mock_response

    client = MagicMock(spec=httpx.Client)
    client.post.side_effect = _fake_post
    set_client(client)
    yield client
    set_client(httpx.Client())