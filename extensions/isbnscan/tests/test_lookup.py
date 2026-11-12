"""
Tests for isbnscan lookup module.

Uses httpx MockTransport to avoid hitting the real Open Library API.
"""

import json
import pytest
import httpx
from httpx import MockTransport

from isbnscan.lookup import (
    clean_isbn,
    is_valid_isbn,
    normalize_isbn,
    lookup_isbn,
    batch_lookup,
    results_to_csv,
    BookResult,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _mock_success(book_data: dict):
    """Return a MockTransport handler that returns a successful Open Library response."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=book_data)
    return MockTransport(handler)


def _mock_error(status: int = 404):
    """Return a MockTransport handler that returns an error."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text="Not Found")
    return MockTransport(handler)


# ── clean_isbn ───────────────────────────────────────────────────────

class TestCleanIsbn:
    def test_strips_dashes(self):
        assert clean_isbn("978-0-14-103614-4") == "9780141036144"

    def test_strips_spaces(self):
        assert clean_isbn("978 0 14 103614 4") == "9780141036144"

    def test_uppercases_x(self):
        assert clean_isbn("0-7475-3269-9x") == "0747532699X"

    def test_keeps_digits_only(self):
        assert clean_isbn("ISBN: 9780141036144") == "9780141036144"


# ── is_valid_isbn ────────────────────────────────────────────────────

class TestIsValidIsbn:
    def test_valid_isbn13(self):
        assert is_valid_isbn("9780141036144") is True

    def test_valid_isbn10(self):
        assert is_valid_isbn("039925537X") is True

    def test_invalid_too_short(self):
        assert is_valid_isbn("123456789") is False

    def test_invalid_too_long(self):
        assert is_valid_isbn("97801410361445") is False

    def test_invalid_alpha_in_isbn13(self):
        assert is_valid_isbn("978014103614A") is False


# ── normalize_isbn ───────────────────────────────────────────────────

class TestNormalizeIsbn:
    def test_returns_cleaned(self):
        assert normalize_isbn("978-0-14-103614-4") == "9780141036144"


# ── lookup_isbn ──────────────────────────────────────────────────────

class TestLookupIsbn:
    def test_successful_lookup(self):
        mock_data = {
            "ISBN:9780141036144": {
                "title": "1984",
                "authors": [{"name": "George Orwell"}],
                "publishers": [{"name": "Penguin"}],
                "publish_date": "2008",
                "number_of_pages": 336,
                "subjects": [{"name": "Dystopian fiction"}],
                "cover": {"large": "https://covers.openlibrary.org/b/id/123-L.jpg"},
            }
        }
        transport = _mock_success(mock_data)
        client = httpx.Client(transport=transport)

        result = lookup_isbn("9780141036144", client=client)
        assert result.found is True
        assert result.title == "1984"
        assert result.authors == "George Orwell"
        assert result.publisher == "Penguin"
        assert result.publish_year == "2008"
        assert result.page_count == "336"
        assert result.subjects == "Dystopian fiction"
        assert result.cover_url == "https://covers.openlibrary.org/b/id/123-L.jpg"

    def test_not_found(self):
        mock_data = {}
        transport = _mock_success(mock_data)
        client = httpx.Client(transport=transport)

        result = lookup_isbn("9780000000000", client=client)
        assert result.found is False
        assert "[NOT FOUND]" in result.title

    def test_http_error(self):
        transport = _mock_error(500)
        client = httpx.Client(transport=transport)

        result = lookup_isbn("9780141036144", client=client)
        assert result.found is False
        assert "[ERROR" in result.title

    def test_handles_missing_fields(self):
        mock_data = {
            "ISBN:9780141036144": {
                "title": "Minimal Book",
            }
        }
        transport = _mock_success(mock_data)
        client = httpx.Client(transport=transport)

        result = lookup_isbn("9780141036144", client=client)
        assert result.found is True
        assert result.title == "Minimal Book"
        assert result.authors == ""
        assert result.publisher == ""
        assert result.publish_year == ""
        assert result.page_count == ""
        assert result.subjects == ""
        assert result.cover_url == ""


# ── batch_lookup ─────────────────────────────────────────────────────

class TestBatchLookup:
    def test_multiple_isbns(self):
        mock_data = {
            "ISBN:9780141036144": {
                "title": "1984",
                "authors": [{"name": "George Orwell"}],
                "publishers": [{"name": "Penguin"}],
                "publish_date": "2008",
                "number_of_pages": 336,
            },
            "ISBN:9780061120084": {
                "title": "To Kill a Mockingbird",
                "authors": [{"name": "Harper Lee"}],
                "publishers": [{"name": "HarperCollins"}],
                "publish_date": "1960",
                "number_of_pages": 281,
            },
        }
        transport = _mock_success(mock_data)
        client = httpx.Client(transport=transport)

        results = batch_lookup(["9780141036144", "9780061120084"], client=client)
        assert len(results) == 2
        assert results[0].title == "1984"
        assert results[1].title == "To Kill a Mockingbird"


# ── results_to_csv ───────────────────────────────────────────────────

class TestResultsToCsv:
    def test_writes_csv(self, tmp_path):
        results = [
            BookResult(
                isbn="9780141036144", title="1984", authors="George Orwell",
                publisher="Penguin", publish_year="2008", page_count="336",
                subjects="Dystopian fiction", cover_url="https://example.com/cover.jpg",
                found=True,
            ),
            BookResult(
                isbn="9780000000000", title="[NOT FOUND]", authors="",
                publisher="", publish_year="", page_count="",
                subjects="", cover_url="", found=False,
            ),
        ]
        csv_path = tmp_path / "results.csv"
        results_to_csv(results, str(csv_path))

        content = csv_path.read_text(encoding="utf-8")
        assert "9780141036144" in content
        assert "George Orwell" in content
        assert "9780000000000" in content
        assert "False" in content  # found=False
