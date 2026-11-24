"""Tests for the story generation engine (mocked API calls)."""

from unittest.mock import patch, MagicMock
import json

from storyweaver.models import StorySession, StoryNode, Choice
from storyweaver.engine import StoryEngine, _build_narration_history


SAMPLE_RESPONSE = json.dumps({
    "narrative": "You enter the dark forest. Shadows flicker between ancient trees.",
    "choices": [
        {"text": "Follow the light", "next_node_id": 2},
        {"text": "Stay on the path", "next_node_id": 3},
        {"text": "Climb a tree", "next_node_id": 4},
    ],
})

SAMPLE_EPILOGUE = "And so the hero's journey came to a close..."


def test_build_narration_history_empty():
    session = StorySession(title="T", genre="G", setting="S", characters="C", premise="P")
    result = _build_narration_history(session)
    assert result == ""


def test_build_narration_history_with_nodes():
    session = StorySession(title="T", genre="G", setting="S", characters="C", premise="P")
    session.add_node(StoryNode(id=1, narrative="First chapter text here"))
    session.add_node(StoryNode(id=2, narrative="Second chapter"))
    result = _build_narration_history(session)
    assert "First chapter" in result
    assert "Second chapter" in result


@patch("storyweaver.engine.requests.post")
def test_generate_first_chapter(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": SAMPLE_RESPONSE}}]
    }
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    engine = StoryEngine(api_key="test-key", api_base="https://fake.api/v1")
    session = StorySession(
        title="Test Tale",
        genre="fantasy",
        setting="Enchanted Forest",
        characters="Elara",
        premise="A mysterious quest",
    )

    node = engine.generate_first_chapter(session)
    assert node.id == 1
    assert "dark forest" in node.narrative
    assert len(node.choices) == 3
    assert node.choices[0].text == "Follow the light"


@patch("storyweaver.engine.requests.post")
def test_generate_next_chapter(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": SAMPLE_RESPONSE}}]
    }
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    engine = StoryEngine(api_key="test-key", api_base="https://fake.api/v1")
    session = StorySession(
        title="T", genre="G", setting="S", characters="C", premise="P"
    )
    session.add_node(StoryNode(id=1, narrative="Start", choices=[
        Choice(text="Go", next_node_id=2),
    ]))

    node = engine.generate_next_chapter(session, "Go")
    assert node.id == 2  # max id was 1, so next is 2
    assert "dark forest" in node.narrative
    assert len(node.choices) == 3


@patch("storyweaver.engine.requests.post")
def test_generate_epilogue(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": SAMPLE_EPILOGUE}}]
    }
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    engine = StoryEngine(api_key="test-key", api_base="https://fake.api/v1")
    session = StorySession(
        title="T", genre="G", setting="S", characters="C", premise="P"
    )
    session.add_node(StoryNode(id=1, narrative="Chapter 1"))

    epilogue = engine.generate_epilogue(session)
    assert "hero's journey" in epilogue


def test_story_engine_init_uses_env_var():
    """Engine should use LLM_API_KEY from environment if no key given."""
    import os
    if "LLM_API_KEY" in os.environ:
        engine = StoryEngine(api_base="https://fake.api/v1")
        assert engine.api_key == os.environ["LLM_API_KEY"]
