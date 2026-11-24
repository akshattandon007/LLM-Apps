"""Tests for the CLI module — argparse and integration smoke tests."""

from unittest.mock import patch
import pytest

from storyweaver.cli import _resolve_saves_dir, _display_node, _get_choice
from storyweaver.models import StoryNode, Choice


def test_resolve_saves_dir():
    """Saves directory is created under home."""
    path = _resolve_saves_dir()
    assert path.exists()
    assert path.name == "saves"
    assert ".storyweaver" in str(path)


def test_display_node_output(capsys):
    """Displaying a node prints narrative and choices."""
    node = StoryNode(id=1, narrative="Hello world", choices=[
        Choice(text="Option A", next_node_id=2),
        Choice(text="Option B", next_node_id=3),
    ])
    _display_node(node)
    captured = capsys.readouterr()
    assert "Hello world" in captured.out
    assert "Option A" in captured.out
    assert "Option B" in captured.out


def test_display_node_no_choices(capsys):
    """A node with no choices still shows narrative."""
    node = StoryNode(id=1, narrative="The end.")
    _display_node(node)
    captured = capsys.readouterr()
    assert "The end." in captured.out


@patch("builtins.input", return_value="1")
def test_get_choice_valid(mock_input):
    node = StoryNode(id=1, narrative="N", choices=[
        Choice(text="A", next_node_id=2),
        Choice(text="B", next_node_id=3),
    ])
    result = _get_choice(node)
    assert result == 0


@patch("builtins.input", return_value="s")
def test_get_choice_save(mock_input):
    node = StoryNode(id=1, narrative="N", choices=[Choice(text="A", next_node_id=2)])
    result = _get_choice(node)
    assert result is None


@patch("builtins.input", side_effect=["0", "2"])
def test_get_choice_retry_on_invalid(mock_input):
    """0 is out of range (1-indexed), should loop until valid."""
    node = StoryNode(id=1, narrative="N", choices=[Choice(text="A", next_node_id=2), Choice(text="B", next_node_id=3)])
    result = _get_choice(node)
    assert result == 1  # "2" → index 1 (Option B)
