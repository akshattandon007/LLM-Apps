"""
tests/test_rag_chain.py
────────────────────────
Tests for the SpendLensAgent — conversation history, source extraction,
and turn counting.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _make_agent():
    """Return a SpendLensAgent with a fully mocked chain."""
    from rag_chain import SpendLensAgent

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "answer": "You spent $45.00 on coffee this month across 3 transactions.",
        "context": [
            MagicMock(metadata={
                "date": "2025-01-15",
                "description": "STARBUCKS COFFEE",
                "amount": -5.75,
                "category": "Dining",
            }),
            MagicMock(metadata={
                "date": "2025-01-20",
                "description": "DUNKIN DONUTS",
                "amount": -12.50,
                "category": "Dining",
            }),
            MagicMock(metadata={
                "date": "2025-01-25",
                "description": "BLUE BOTTLE COFFEE",
                "amount": -26.75,
                "category": "Dining",
            }),
        ],
    }
    return SpendLensAgent(chain=mock_chain, llm_name="claude-sonnet-4-5")


def test_agent_ask_returns_answer():
    agent = _make_agent()
    result = agent.ask("How much did I spend on coffee this month?")
    assert "coffee" in result["answer"].lower()
    assert "$45.00" in result["answer"]


def test_agent_ask_deduplicates_sources():
    agent = _make_agent()
    result = agent.ask("What are my dining expenses?")
    # Three unique transactions → three sources
    assert len(result["sources"]) == 3


def test_agent_ask_sources_have_metadata():
    agent = _make_agent()
    result = agent.ask("Show me my coffee spend")
    for src in result["sources"]:
        assert "date" in src or "description" in src or "amount" in src


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
    calls = agent._chain.invoke.call_args_list
    second_call_kwargs = calls[1][0][0]
    assert len(second_call_kwargs["chat_history"]) == 2  # 1 Q + 1 A


def test_agent_reset_clears_history():
    agent = _make_agent()
    agent.ask("Some question")
    assert agent.turn_count == 1
    agent.reset_history()
    assert agent.turn_count == 0
    assert agent._history == []


def test_agent_history_capped_at_20_messages():
    agent = _make_agent()
    for i in range(15):
        agent.ask(f"Question {i}")
    assert len(agent._history) <= 20


def test_agent_handles_empty_answer():
    from rag_chain import SpendLensAgent

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "", "context": []}
    agent = SpendLensAgent(chain=mock_chain, llm_name="test")

    result = agent.ask("Anything?")
    assert result["answer"] == ""
    assert result["sources"] == []
