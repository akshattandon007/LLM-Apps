"""Tests for the StoryWeaver data models."""

import json
import tempfile
from pathlib import Path

from storyweaver.models import StorySession, StoryNode, Choice


def test_create_story_session():
    """A new session has default values."""
    session = StorySession(
        title="Test Tale",
        genre="fantasy",
        setting="Enchanted Forest",
        characters="Elara the elf",
        premise="A journey begins",
    )
    assert session.title == "Test Tale"
    assert session.genre == "fantasy"
    assert session.nodes == []
    assert session.current_node_id == 0
    assert session.history == []


def test_add_node():
    """Adding a node sets it as current and updates timestamps."""
    session = StorySession(title="T", genre="G", setting="S", characters="C", premise="P")
    node = StoryNode(id=1, narrative="Once upon a time...", choices=[
        Choice(text="Go left", next_node_id=2),
        Choice(text="Go right", next_node_id=3),
    ])
    session.add_node(node)
    assert len(session.nodes) == 1
    assert session.current_node_id == 1
    assert session.get_current_node() is node


def test_get_current_node_returns_none_when_empty():
    session = StorySession(title="T", genre="G", setting="S", characters="C", premise="P")
    assert session.get_current_node() is None


def test_make_choice_valid():
    session = StorySession(title="T", genre="G", setting="S", characters="C", premise="P")
    node = StoryNode(id=1, narrative="Start", choices=[
        Choice(text="Path A", next_node_id=2),
        Choice(text="Path B", next_node_id=3),
    ])
    session.add_node(node)

    chosen = session.make_choice(0)
    assert chosen is not None
    assert chosen.text == "Path A"
    assert chosen.next_node_id == 2
    assert session.current_node_id == 2
    assert session.history == [1]


def test_make_choice_out_of_range():
    session = StorySession(title="T", genre="G", setting="S", characters="C", premise="P")
    node = StoryNode(id=1, narrative="Start", choices=[Choice(text="Only", next_node_id=2)])
    session.add_node(node)

    assert session.make_choice(5) is None
    assert session.make_choice(-1) is None


def test_save_and_load():
    """Round-trip save and load a session with multiple nodes."""
    session = StorySession(
        title="Save Test",
        genre="sci-fi",
        setting="Mars Colony",
        characters="Captain Zara",
        premise="First contact",
    )
    session.add_node(StoryNode(id=1, narrative="Chapter 1", choices=[
        Choice(text="Explore", next_node_id=2),
    ]))
    session.add_node(StoryNode(id=2, narrative="Chapter 2", choices=[
        Choice(text="Fight", next_node_id=3),
        Choice(text="Flee", next_node_id=4),
    ]))
    session.current_node_id = 2
    session.history = [1]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
        session.save(path)

    loaded = StorySession.load(path)
    assert loaded.title == "Save Test"
    assert loaded.genre == "sci-fi"
    assert loaded.current_node_id == 2
    assert loaded.history == [1]
    assert len(loaded.nodes) == 2
    assert loaded.nodes[0].narrative == "Chapter 1"
    assert len(loaded.nodes[0].choices) == 1
    assert loaded.nodes[0].choices[0].text == "Explore"

    Path(path).unlink()


def test_to_dict_roundtrip():
    session = StorySession(title="T", genre="G", setting="S", characters="C", premise="P")
    session.add_node(StoryNode(id=1, narrative="N1", choices=[Choice(text="C1", next_node_id=2)]))

    d = session.to_dict()
    assert d["title"] == "T"
    assert d["nodes"][0]["narrative"] == "N1"
    assert d["nodes"][0]["choices"][0]["text"] == "C1"

    restored = StorySession.from_dict(d)
    assert restored.title == "T"
    assert restored.nodes[0].narrative == "N1"


def test_multiple_choices_per_node():
    node = StoryNode(id=1, narrative="Branch point", choices=[
        Choice(text="Up", next_node_id=10),
        Choice(text="Down", next_node_id=11),
        Choice(text="Side", next_node_id=12),
    ])
    assert len(node.choices) == 3
    assert node.choices[1].text == "Down"
    assert node.choices[2].next_node_id == 12
