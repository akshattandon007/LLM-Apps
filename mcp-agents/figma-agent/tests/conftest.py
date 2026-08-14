"""Pytest fixture: run setup() before each test so the fake Figma client is installed."""
import pytest

from tests.test_smoke import setup


@pytest.fixture(autouse=True)
def _figma_setup():
    setup()
    yield