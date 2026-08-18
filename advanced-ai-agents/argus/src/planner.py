"""Research planner — decomposes a user query into sub-questions."""

from __future__ import annotations

from src.models import SubQuestion

# Module-level client — injectable for tests.
_client = None


def set_client(client):
    """Inject a mock/fake client for testing."""
    global _client
    _client = client


def _get_client():
    """Return the injected client or fall back to the built-in planner logic."""
    return _client


def plan_query(query: str) -> list[SubQuestion]:
    """Decompose a research query into sub-questions.

    Uses a prompt-based decomposition approach. In simulated mode (no real
    LLM client), falls back to heuristic decomposition.
    """
    client = _get_client()
    if client is not None:
        return client.plan_query(query)

    # Heuristic decomposition when no LLM client is configured.
    return _decompose_heuristic(query)


def _decompose_heuristic(query: str) -> list[SubQuestion]:
    """Simple rule-based decomposition for the thin slice."""
    sub_questions = [
        SubQuestion(
            question=f"What are the key facts, definitions, and background about: {query}?",
            intent="Establish baseline facts and definitions",
            priority=1,
        ),
        SubQuestion(
            question=f"What is the current state of research or development in: {query}?",
            intent="Survey recent developments",
            priority=2,
        ),
        SubQuestion(
            question=f"What controversies, debates, or alternative viewpoints exist around: {query}?",
            intent="Identify disagreements and open questions",
            priority=3,
        ),
        SubQuestion(
            question=f"What are the practical implications, applications, or future directions of: {query}?",
            intent="Synthesize forward-looking insights",
            priority=4,
        ),
    ]
    return sub_questions