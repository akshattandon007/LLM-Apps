"""Pytest fixture: run setup() before each test so the fake Gmail client is installed."""
import pytest

from tests.test_smoke import setup


@pytest.fixture(autouse=True)
def _inbox_setup():
    setup()
    yield
