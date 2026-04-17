"""Shared pytest fixtures for SketchIt backend tests."""

import os
import sys

import pytest

# Make the backend package importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Provide a Flask app instance configured for testing."""
    # Ensure the API key isn't required for tests that don't hit Claude
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")
    from server import app as flask_app

    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
