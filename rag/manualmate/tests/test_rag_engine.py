"""Tests for the RAG engine — with mocked OpenAI API calls."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock


class FakeEmbedding:
    """Simulates an OpenAI embedding response."""
    def __init__(self, dim=384):
        self.embedding = [0.01] * dim


class FakeEmbeddingResponse:
    def __init__(self, n, dim=384):
        self.data = [FakeEmbedding(dim) for _ in range(n)]


class FakeChoice:
    def __init__(self, text="Here is the answer based on the manual."):
        self.message = MagicMock()
        self.message.content = text


class FakeChatResponse:
    def __init__(self, text="Here is the answer based on the manual."):
        self.choices = [FakeChoice(text)]
        self.usage = MagicMock()


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client and patch the constructor."""
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = FakeEmbeddingResponse(1)
    mock_client.chat.completions.create.return_value = FakeChatResponse()
    return mock_client


@pytest.fixture
def engine(monkeypatch, mock_openai_client):
    """Create engine with mocked OpenAI API."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")
    # Patch openai.OpenAI constructor to return our mock
    monkeypatch.setattr("openai.OpenAI", lambda **kw: mock_openai_client)
    engine = __import__("manualmate").rag_engine.ManualMateRAG(
        store_dir="/tmp/.manualmate_test"
    )
    engine.clear()
    return engine


@pytest.fixture
def engine_no_mock(monkeypatch):
    """Engine with a fake API key (no mocks) — only for testing non-API paths."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")
    engine = __import__("manualmate").rag_engine.ManualMateRAG(
        store_dir="/tmp/.manualmate_test"
    )
    engine.clear()
    return engine


class TestManualMateRAG:
    def test_init_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            __import__("manualmate").rag_engine.ManualMateRAG(
                store_dir="/tmp/.manualmate_test_nokey"
            )

    def test_ingest_txt(self, engine):
        """Test ingesting a text file with mocked embeddings."""
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("""Refrigerator User Manual
Model: CoolMaster 3000
Error Code E24: This indicates a freezer temperature sensor failure.
To fix: Unplug the unit for 30 seconds, then plug back in.
If the error persists, contact customer service.
Regular maintenance: Clean condenser coils every 6 months.""")
            fpath = f.name

        try:
            result = engine.ingest(fpath)
            assert result.chunks > 0
            assert result.characters > 0

            # Verify it's in the store
            docs = engine.list_docs()
            assert len(docs) > 0
        finally:
            os.unlink(fpath)
            engine.clear()

    def test_ask_returns_answer(self, engine):
        """Test asking a question returns formatted results."""
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Washer Error Code E24: Drain pump failure. Check drain hose for clogs.")
            fpath = f.name

        try:
            engine.ingest(fpath)
            result = engine.ask("What does error code E24 mean?")
            assert result.answer
            assert len(result.sources) > 0
            assert len(result.chunks) > 0
        finally:
            os.unlink(fpath)
            engine.clear()

    def test_ask_no_data_returns_empty(self, engine_no_mock):
        """Asking without any data returns guidance message."""
        result = engine_no_mock.ask("What is the error code for drain pump?")
        assert "No relevant documents found" in result.answer
        assert result.sources == []
        assert result.chunks == []

    def test_list_docs_empty(self, engine_no_mock):
        docs = engine_no_mock.list_docs()
        assert isinstance(docs, list)
        assert len(docs) == 0

    def test_remove_nonexistent(self, engine_no_mock):
        assert engine_no_mock.remove_doc("nonexistent.txt") is False

    def test_clear(self, engine_no_mock):
        engine_no_mock.clear()
        assert engine_no_mock.list_docs() == []
        assert engine_no_mock.store.chunks == []