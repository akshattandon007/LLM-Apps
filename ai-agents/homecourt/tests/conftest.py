"""Pytest fixtures for HomeCourt smoke tests."""

import pytest

from src.models import Case, CasePlea


@pytest.fixture
def sushi_vs_pizza() -> Case:
    """Classic daily-life dilemma."""
    return Case(
        title="Sushi vs Pizza",
        pleas=[
            CasePlea(side="Alice", argument="Sushi is fresh, healthy, and elegant."),
            CasePlea(side="Bob", argument="Pizza is happiness in triangle form."),
        ],
    )


@pytest.fixture
def text_mom_now_vs_later() -> Case:
    """Relatability test case."""
    return Case(
        title="Text Mom Now vs Tomorrow",
        pleas=[
            CasePlea(side="Responsible Child", argument="She's your mother. Reply now."),
            CasePlea(side="Busy Adult", argument="Tomorrow is fine. Everyone survives."),
        ],
    )


@pytest.fixture
def all_persona_keys() -> list[str]:
    """Return all valid persona keys for parametrised tests."""
    from src.personas import PERSONAS
    return [p.key.value for p in PERSONAS]