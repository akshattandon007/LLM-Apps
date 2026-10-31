"""
BookWorm MCP Server — Book search and discovery via Open Library.

Exposes MCP tools for searching books, looking up details, author info,
subject browsing, and cover images. Uses Open Library's free public API
(no authentication required).
"""

from __future__ import annotations

import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from .open_library_client import OpenLibraryClient

# ── MCP Server ──────────────────────────────────────────────────────────

mcp = FastMCP("BookWorm MCP")

# Reusable client instance (lazily created)
_client: OpenLibraryClient | None = None


def get_client() -> OpenLibraryClient:
    global _client
    if _client is None:
        _client = OpenLibraryClient()
    return _client


# ── Helper: clean Open Library data for MCP output ──────────────────────


def _clean_book_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """Extract clean fields from a search result document."""
    cover_id = doc.get("cover_i")
    cover_url = (
        f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
        if cover_id
        else None
    )
    return {
        "key": doc.get("key"),
        "title": doc.get("title"),
        "author": (doc.get("author_name") or ["Unknown"])[0],
        "first_publish_year": doc.get("first_publish_year"),
        "isbn": (doc.get("isbn") or [None])[0],
        "cover_url": cover_url,
        "edition_count": doc.get("edition_count"),
        "subject": (doc.get("subject") or [])[:5],
        "language": (doc.get("language") or [])[:3],
    }


def _clean_edition(ed: dict[str, Any]) -> dict[str, Any]:
    """Extract clean fields from an edition record."""
    return {
        "key": ed.get("key"),
        "title": ed.get("title"),
        "publish_date": ed.get("publish_date"),
        "publishers": ed.get("publishers", []),
        "isbn_10": (ed.get("isbn_10") or [None])[0],
        "isbn_13": (ed.get("isbn_13") or [None])[0],
        "pages": ed.get("number_of_pages") or ed.get("pagination"),
        "cover_url": (
            f"https://covers.openlibrary.org/b/olid/{ed['key'].split('/')[-1]}-M.jpg"
            if ed.get("key")
            else None
        ),
    }


# ── MCP Tools ───────────────────────────────────────────────────────────


@mcp.tool()
def search_books(query: str, limit: int = 10, page: int = 1) -> list[dict[str, Any]]:
    """Search for books by title, author, or keywords.

    Returns a list of matching books with title, author, year, ISBN, and cover URL.
    """
    client = get_client()
    result = client.search_books(query, limit=limit, page=page)
    docs = result.get("docs", [])
    num_found = result.get("numFound", 0)
    cleaned = [_clean_book_doc(d) for d in docs[:limit]]
    return [
        {"total_results": num_found, "page": page, "results_returned": len(cleaned)},
        *cleaned,
    ]


@mcp.tool()
def get_book(isbn: str = "", olid: str = "") -> dict[str, Any]:
    """Get detailed book information by ISBN (10 or 13 digits) or Open Library ID (e.g. OL123M).

    Provide exactly one identifier. Returns edition details including title,
    publishers, page count, ISBNs, and cover URL.
    """
    client = get_client()
    if isbn:
        raw = client.get_book_by_isbn(isbn)
        key = f"ISBN:{isbn}"
        data = raw.get(key, {})
        if not data or "error" in str(data).lower():
            return {"error": f"Book not found for ISBN: {isbn}"}
        cover_id = data.get("cover", {}).get("small", "")
        return {
            "title": data.get("title", data.get("name", "")),
            "authors": [a.get("name", "") for a in (data.get("authors") or [])],
            "publish_date": data.get("publish_date"),
            "publishers": data.get("publishers", []),
            "pages": data.get("number_of_pages"),
            "subtitle": data.get("subtitle"),
            "cover_url": (
                f"https:covers.openlibrary.org{cover_id}" if cover_id else None
            ),
            "url": data.get("info_url"),
        }
    elif olid:
        edition = client.get_book_by_olid(olid)
        return _clean_edition(edition)
    return {"error": "Provide either isbn or olid."}


@mcp.tool()
def get_author(author_id: str, include_works: bool = True) -> dict[str, Any]:
    """Get author details by Open Library Author ID (e.g. OL23919A).

    Returns name, birth/death dates, bio, and optionally their notable works.
    """
    client = get_client()
    author = client.get_author(author_id)
    photo_url = client.get_author_photo_url(author_id)
    result = {
        "key": author.get("key"),
        "name": author.get("name"),
        "birth_date": author.get("birth_date"),
        "death_date": author.get("death_date"),
        "bio": (
            author.get("bio", "")
            if isinstance(author.get("bio"), str)
            else (author.get("bio", {}).get("value", "") if author.get("bio") else "")
        ),
        "photo_url": photo_url,
        "personal_name": author.get("personal_name"),
        "wikipedia": author.get("wikipedia"),
    }
    if include_works:
        works = client.get_author_works(author_id, limit=10)
        result["notable_works"] = [
            {
                "title": w.get("title"),
                "key": w.get("key"),
                "first_publish_year": w.get("first_publish_year"),
            }
            for w in (works.get("entries", [])[:10] if "entries" in works else works.get("works", [])[:10])
        ]
    return result


@mcp.tool()
def search_subject(subject: str, limit: int = 10, page: int = 1) -> list[dict[str, Any]]:
    """Search for books by subject or topic (e.g. 'fantasy', 'cooking', 'space').

    Returns books in that subject category with title, author, and year.
    """
    client = get_client()
    result = client.search_subject(subject, limit=limit, page=page)
    works = result.get("works", [])
    cleaned = [_clean_book_doc(w) for w in works[:limit]]
    return [
        {
            "subject": subject,
            "total_works": result.get("work_count", 0),
            "results_returned": len(cleaned),
        },
        *cleaned,
    ]


@mcp.tool()
def search_authors(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search for authors by name.

    Returns matching authors with their key, name, birth/death dates, and top subjects.
    """
    client = get_client()
    result = client.search_authors(query, limit=limit)
    docs = result.get("docs", [])
    cleaned = []
    for doc in docs[:limit]:
        cleaned.append({
            "key": doc.get("key"),
            "name": doc.get("name") or doc.get("author_name", [""])[0],
            "birth_date": doc.get("birth_date"),
            "death_date": doc.get("death_date"),
            "top_subjects": (doc.get("top_subjects") or [])[:5],
            "work_count": doc.get("work_count"),
        })
    return [
        {"total_results": result.get("numFound", 0), "results_returned": len(cleaned)},
        *cleaned,
    ]


@mcp.tool()
def get_book_cover(olid: str, size: str = "M") -> str:
    """Get the cover image URL for a book edition.

    Args:
        olid: Open Library ID (e.g. OL123M)
        size: Cover size — S (small), M (medium), L (large)

    Returns the cover image URL.
    """
    client = get_client()
    return client.get_book_cover_url(olid, size)


@mcp.tool()
def get_trending(limit: int = 10) -> list[dict[str, Any]]:
    """Get currently trending/popular books from Open Library.

    Returns recent high-activity books with title, author, year, and cover URL.
    """
    client = get_client()
    result = client.get_trending(limit)
    docs = result.get("docs", [])
    cleaned = [_clean_book_doc(d) for d in docs[:limit]]
    return [
        {"total_results": min(len(cleaned), limit), "results_returned": len(cleaned)},
        *cleaned,
    ]


# ── Entry point ─────────────────────────────────────────────────────────


def main() -> None:
    """Run the BookWorm MCP server over stdio."""
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        if _client:
            _client.close()
        sys.exit(0)


if __name__ == "__main__":
    main()