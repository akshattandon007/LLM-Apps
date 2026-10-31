"""Tests for BookWorm MCP Server."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bookworm.open_library_client import OpenLibraryClient
from bookworm.server import _clean_book_doc, _clean_edition, get_client


# ── OpenLibraryClient tests ─────────────────────────────────────────────


@pytest.fixture
def mock_client():
    """Provide an OpenLibraryClient with a mocked httpx client."""
    cli = OpenLibraryClient()
    cli.client = MagicMock()
    cli.rate_limiter = MagicMock()  # disable rate limiting in tests
    return cli


class TestSearchBooks:
    def test_search_success(self, mock_client):
        mock_client.client.get.return_value.json.return_value = {
            "numFound": 1,
            "docs": [
                {
                    "key": "/works/OL123W",
                    "title": "The Hobbit",
                    "author_name": ["J.R.R. Tolkien"],
                    "first_publish_year": 1937,
                    "isbn": ["1234567890"],
                    "edition_count": 120,
                    "subject": ["Fantasy", "Adventure"],
                    "language": ["eng"],
                    "cover_i": 12345,
                }
            ],
        }
        result = mock_client.search_books("hobbit")
        assert result["numFound"] == 1
        assert result["docs"][0]["title"] == "The Hobbit"

    def test_search_empty(self, mock_client):
        mock_client.client.get.return_value.json.return_value = {
            "numFound": 0,
            "docs": [],
        }
        result = mock_client.search_books("xyzzy")
        assert result["numFound"] == 0

    def test_search_with_pagination(self, mock_client):
        mock_client.client.get.return_value.json.return_value = {
            "numFound": 2,
            "docs": [
                {"key": "/works/OL1W", "title": "Book A"},
                {"key": "/works/OL2W", "title": "Book B"},
            ],
        }
        result = mock_client.search_books("test", limit=2, page=1)
        assert len(result["docs"]) == 2


class TestGetBook:
    def test_by_isbn(self, mock_client):
        mock_client.client.get.return_value.json.return_value = {
            "ISBN:0451526538": {
                "title": "The Hobbit",
                "authors": [{"name": "J.R.R. Tolkien"}],
                "publish_date": "1937",
                "number_of_pages": 310,
            }
        }
        result = mock_client.get_book_by_isbn("0451526538")
        assert "ISBN:0451526538" in result
        assert result["ISBN:0451526538"]["title"] == "The Hobbit"

    def test_by_olid(self, mock_client):
        mock_client.client.get.return_value.json.return_value = {
            "key": "/books/OL123M",
            "title": "Test Book",
            "publishers": ["Test Publisher"],
            "number_of_pages": 200,
        }
        result = mock_client.get_book_by_olid("OL123M")
        assert result["title"] == "Test Book"


class TestAuthor:
    def test_get_author(self, mock_client):
        mock_client.client.get.return_value.json.return_value = {
            "key": "/authors/OL23919A",
            "name": "J.R.R. Tolkien",
            "birth_date": "3 January 1892",
            "death_date": "2 September 1973",
        }
        result = mock_client.get_author("OL23919A")
        assert result["name"] == "J.R.R. Tolkien"
        assert "birth_date" in result

    def test_author_works(self, mock_client):
        mock_client.client.get.return_value.json.return_value = {
            "entries": [
                {"title": "The Hobbit", "key": "/works/OL123W", "first_publish_year": 1937}
            ]
        }
        result = mock_client.get_author_works("OL23919A")
        assert len(result["entries"]) == 1


class TestSubject:
    def test_search_subject(self, mock_client):
        mock_client.client.get.return_value.json.return_value = {
            "work_count": 50,
            "works": [
                {
                    "key": "/works/OL1W",
                    "title": "Fantasy Book",
                    "author_name": ["Author"],
                    "first_publish_year": 2000,
                    "subject": ["Fantasy"],
                    "language": ["eng"],
                }
            ],
        }
        result = mock_client.search_subject("fantasy")
        assert result["work_count"] == 50


# ── Helper function tests ───────────────────────────────────────────────


class TestCleanBookDoc:
    def test_cleans_fields(self):
        doc = {
            "key": "/works/OL123W",
            "title": "Test",
            "author_name": ["Author"],
            "first_publish_year": 2000,
            "isbn": ["12345"],
            "edition_count": 5,
            "subject": ["A", "B", "C", "D", "E", "F"],
            "language": ["eng", "spa"],
            "cover_i": 999,
        }
        cleaned = _clean_book_doc(doc)
        assert cleaned["title"] == "Test"
        assert cleaned["author"] == "Author"
        assert len(cleaned["subject"]) == 5
        assert "cover_url" in cleaned

    def test_missing_fields(self):
        doc = {}
        cleaned = _clean_book_doc(doc)
        assert cleaned["title"] is None
        assert cleaned["author"] == "Unknown"


class TestCleanEdition:
    def test_cleans_edition(self):
        ed = {
            "key": "/books/OL123M",
            "title": "Edition",
            "publishers": ["Pub"],
            "isbn_10": ["1234567890"],
            "number_of_pages": 300,
        }
        cleaned = _clean_edition(ed)
        assert cleaned["title"] == "Edition"
        assert cleaned["pages"] == 300

    def test_missing_pages(self):
        ed = {"key": "/books/OL1M", "title": "No Pages"}
        cleaned = _clean_edition(ed)
        assert cleaned["pages"] is None


# ── Server tool tests (integration via client flow) ─────────────────────


class TestServerTools:
    @patch("bookworm.server.get_client")
    def test_search_books_tool(self, mock_get_client):
        """Test the search_books MCP tool logic through its data flow."""
        mock_cli = MagicMock()
        mock_get_client.return_value = mock_cli
        mock_cli.search_books.return_value = {
            "numFound": 1,
            "docs": [
                {
                    "key": "/works/OL1W",
                    "title": "Test Book",
                    "author_name": ["Author"],
                    "first_publish_year": 2001,
                    "isbn": ["111"],
                    "edition_count": 3,
                    "subject": ["Fiction"],
                    "language": ["eng"],
                    "cover_i": 1,
                }
            ],
        }

        from bookworm.server import search_books

        result = search_books("test")
        assert len(result) == 2
        assert result[0]["total_results"] == 1
        assert result[1]["title"] == "Test Book"


@pytest.mark.integration
class TestLiveAPI:
    """Integration tests against real Open Library API.

    These are skipped by default. Run with: pytest -x -m integration
    """

    def test_live_search(self):
        cli = OpenLibraryClient()
        result = cli.search_books("the hobbit", limit=1)
        assert result["numFound"] > 0
        cli.close()

    def test_live_isbn_lookup(self):
        cli = OpenLibraryClient()
        result = cli.get_book_by_isbn("0451526538")
        assert "ISBN:0451526538" in result
        cli.close()

    def test_live_author(self):
        cli = OpenLibraryClient()
        result = cli.get_author("OL23919A")
        assert "Rowling" in result["name"]  # OL23919A = J.K. Rowling
        cli.close()