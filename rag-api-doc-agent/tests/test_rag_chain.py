"""
tests/test_rag_chain.py
────────────────────────
Tests for the RAGAgent stateful wrapper — conversation history,
source extraction, and turn counting.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _make_agent():
    """Return a RAGAgent with a fully mocked chain."""
    # Import here after sys.path is set
    from rag_chain import RAGAgent

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "answer": "The Graph API lets you read/write Facebook data via HTTP.",
        "context": [
            MagicMock(metadata={"source": "https://developers.facebook.com/docs/graph-api/"}),
            MagicMock(metadata={"source": "https://developers.facebook.com/docs/graph-api/"}),
            MagicMock(metadata={"source": "https://developers.facebook.com/docs/graph-api/overview/"}),
        ],
    }
    return RAGAgent(chain=mock_chain, llm_name="claude-sonnet-4-5")


def test_agent_ask_returns_answer():
    agent = _make_agent()
    result = agent.ask("What is the Graph API?")
    assert result["answer"].startswith("The Graph API")


def test_agent_ask_deduplicates_sources():
    agent = _make_agent()
    result = agent.ask("What is the Graph API?")
    # Two identical source URLs should collapse into one
    unique_sources = list(dict.fromkeys(result["sources"]))
    assert result["sources"] == unique_sources


def test_agent_turn_count_increments():
    agent = _make_agent()
    assert agent.turn_count == 0
    agent.ask("Question 1")
    assert agent.turn_count == 1
    agent.ask("Question 2")
    assert agent.turn_count == 2


def test_agent_history_is_passed_to_chain():
    agent = _make_agent()
    agent.ask("First question")
    agent.ask("Follow-up question")
    # History should have been included in the second call
    calls = agent._chain.invoke.call_args_list
    second_call_kwargs = calls[1][0][0]
    assert len(second_call_kwargs["chat_history"]) == 2  # 1 Q + 1 A from turn 1


def test_agent_reset_clears_history():
    agent = _make_agent()
    agent.ask("Some question")
    assert agent.turn_count == 1
    agent.reset_history()
    assert agent.turn_count == 0
    assert agent._history == []


def test_agent_history_capped_at_20_messages():
    agent = _make_agent()
    # Ask 15 questions — would produce 30 messages without capping
    for i in range(15):
        agent.ask(f"Question {i}")
    # History should be capped
    assert len(agent._history) <= 20
