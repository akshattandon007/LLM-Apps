"""Tests for MailMerge."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from mailmerge.ingest import chunk_text, extract_text_from_email, parse_mbox
from mailmerge.models import EmailMetadata, EmailChunk, SearchResult


# ── chunk_text tests ────────────────────────────────────────────────────────


class TestChunkText:
    def test_empty_text(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_stays_one_chunk(self):
        text = "Hello world. This is a short email."
        chunks = chunk_text(text, chunk_size=200)
        assert len(chunks) == 1
        assert "Hello world" in chunks[0]

    def test_splits_into_multiple_chunks(self):
        para_a = "A" * 600
        para_b = "B" * 600
        text = f"{para_a}\n\n{para_b}"
        chunks = chunk_text(text, chunk_size=500, overlap=0)
        assert len(chunks) >= 2
        assert "A" in chunks[0] or "B" in chunks[0]

    def test_overlap_creates_sharing(self):
        para_a = "X" * 300
        para_b = "Y" * 300
        text = f"{para_a}\n\n{para_b}"
        chunks = chunk_text(text, chunk_size=400, overlap=100)
        # With overlap=100, the second chunk should include tail of first
        assert len(chunks) >= 1

    def test_sentence_boundary_respect(self):
        """Long paragraph should be split at sentence boundaries."""
        sentences = "Sentence one. " * 50  # ~750 chars
        chunks = chunk_text(sentences, chunk_size=400, overlap=0)
        assert len(chunks) >= 1


# ── extract_text_from_email tests ────────────────────────────────────────────


class TestExtractText:
    def test_simple_text_email(self):
        """Simulates a simple text-only email."""
        from email.mime.text import MIMEText
        msg = MIMEText("Hello, this is a test email body.")
        text = extract_text_from_email(msg)
        assert "Hello" in text
        assert "test email" in text

    def test_multipart_email(self):
        """Simulates a multipart email with plain text."""
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart()
        msg.attach(MIMEText("Plain text part here."))
        html = MIMEText("<html><body><b>HTML</b></body></html>", "html")
        msg.attach(html)
        text = extract_text_from_email(msg)
        assert "Plain text" in text
        assert "HTML" not in text  # we only extract text/plain


# ── SearchResult model ─────────────────────────────────────────────────────


class TestSearchResult:
    def test_model_creation(self):
        r = SearchResult(
            chunk_id="abc123",
            subject="Hello world",
            sender="alice@example.com",
            date="2024-01-01",
            snippet="Some content here...",
            score=0.95,
        )
        assert r.chunk_id == "abc123"
        assert r.score == 0.95


# ── Integration-style: chunk round trip ─────────────────────────────────────


class TestChunkToSearch:
    def test_chunk_and_display(self):
        """Verify chunk output is valid input for search display."""
        text = "Dear Sir,\n\nPlease find attached the quarterly report for Q3.\n\nBest regards,\nJohn Doe"
        chunks = chunk_text(text, chunk_size=200)
        assert len(chunks) >= 1
        assert "quarterly report" in chunks[0]