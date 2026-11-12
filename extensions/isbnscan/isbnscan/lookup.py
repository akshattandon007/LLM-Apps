"""
ISBN lookup logic — queries the Open Library Books API.

Open Library API: https://openlibrary.org/api/books?bibkeys=ISBN:...&format=json
Free, no API key required.
"""

import csv
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import quote

import httpx

OPEN_LIBRARY_API = "https://openlibrary.org/api/books"
USER_AGENT = "isbnscan/1.0 (CLI book lookup tool; mailto:user@example.com)"

# Regex to strip non-digit characters from ISBNs
ISBN_CLEAN = re.compile(r"[^\dXx]")


@dataclass
class BookResult:
    """Result of an ISBN lookup."""

    isbn: str
    title: str
    authors: str
    publisher: str
    publish_year: str
    page_count: str
    subjects: str
    cover_url: str
    found: bool = True


def clean_isbn(raw: str) -> str:
    """Strip non-digit characters; upper-case trailing X."""
    cleaned = ISBN_CLEAN.sub("", raw).upper()
    return cleaned


def is_valid_isbn(isbn: str) -> bool:
    """Basic ISBN-10 or ISBN-13 format check (length + digits)."""
    cleaned = clean_isbn(isbn)
    if len(cleaned) == 10:
        return bool(re.match(r"^\d{9}[\dX]$", cleaned))
    elif len(cleaned) == 13:
        return bool(re.match(r"^\d{13}$", cleaned))
    return False


def normalize_isbn(isbn: str) -> str:
    """Return clean ISBN (ISBN-13 preferred)."""
    return clean_isbn(isbn)


def lookup_isbn(isbn: str, client: Optional[httpx.Client] = None) -> BookResult:
    """
    Look up a single ISBN via the Open Library Books API.
    Returns a BookResult (found=True on success, found=False on miss/error).
    """
    raw_isbn = isbn
    cleaned = clean_isbn(isbn)
    bibkey = f"ISBN:{cleaned}"
    params = {"bibkeys": bibkey, "format": "json", "jscmd": "data"}
    headers = {"User-Agent": USER_AGENT}

    close_client = False
    if client is None:
        client = httpx.Client()
        close_client = True

    try:
        resp = client.get(OPEN_LIBRARY_API, params=params, headers=headers, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()

        if bibkey not in data or data[bibkey] is None:
            return BookResult(
                isbn=raw_isbn,
                title="[NOT FOUND]",
                authors="",
                publisher="",
                publish_year="",
                page_count="",
                subjects="",
                cover_url="",
                found=False,
            )

        entry = data[bibkey]
        title = entry.get("title", "[UNTITLED]")
        authors = ", ".join(
            a.get("name", "") for a in entry.get("authors", [])
        )
        publishers = ", ".join(
            p.get("name", "") for p in entry.get("publishers", [])
        )
        publish_date = entry.get("publish_date", "")
        # Extract year from publish_date string
        year_match = re.search(r"\d{4}", publish_date)
        publish_year = year_match.group(0) if year_match else publish_date

        # Page count
        page_count = ""
        if "number_of_pages" in entry:
            page_count = str(entry["number_of_pages"])

        # Subjects
        subjects = ", ".join(
            s.get("name", "") for s in entry.get("subjects", [])
        )

        # Cover image
        cover_url = ""
        if "cover" in entry:
            cover_url = entry["cover"].get("large", entry["cover"].get("medium", entry["cover"].get("small", "")))

        return BookResult(
            isbn=raw_isbn,
            title=title,
            authors=authors,
            publisher=publishers,
            publish_year=publish_year,
            page_count=page_count,
            subjects=subjects,
            cover_url=cover_url,
            found=True,
        )

    except (httpx.HTTPError, httpx.TimeoutException, json.JSONDecodeError) as exc:
        return BookResult(
            isbn=raw_isbn,
            title=f"[ERROR: {exc}]",
            authors="",
            publisher="",
            publish_year="",
            page_count="",
            subjects="",
            cover_url="",
            found=False,
        )
    finally:
        if close_client:
            client.close()


def batch_lookup(isbns: list[str], client: Optional[httpx.Client] = None) -> list[BookResult]:
    """Look up a list of ISBNs. Each ISBN is looked up individually."""
    results = []
    for isbn in isbns:
        result = lookup_isbn(isbn, client=client)
        results.append(result)
    return results


def results_to_csv(results: list[BookResult], path: str) -> None:
    """Write results to a CSV file."""
    fieldnames = [
        "isbn", "found", "title", "authors", "publisher",
        "publish_year", "page_count", "subjects", "cover_url",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = asdict(r)
            writer.writerow(row)
