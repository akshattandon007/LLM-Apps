"""
src/document_loader.py
──────────────────────
Responsible for fetching, parsing, and chunking API documentation
from a given URL. Handles multi-page crawling for doc sites.
"""

from __future__ import annotations

import re
import time
from typing import List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# ─── Constants ────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; APIDocRAGBot/1.0; "
        "+https://github.com/your-org/api-rag-agent)"
    )
}
REQUEST_TIMEOUT = 15          # seconds per page fetch
MAX_PAGES = 30                # cap crawl at 30 linked pages
CRAWL_DELAY = 0.5             # polite delay between requests (seconds)

# Tags that typically contain meaningful doc content
CONTENT_TAGS = ["article", "main", "section", "div[role='main']"]

# Tags to strip (nav, ads, footers add noise)
NOISE_TAGS = [
    "nav", "footer", "header", "aside",
    "script", "style", "noscript",
    "[class*='sidebar']", "[class*='menu']", "[class*='cookie']",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clean_text(raw: str) -> str:
    """Collapse whitespace and strip boilerplate line noise."""
    lines = [line.strip() for line in raw.splitlines()]
    # Remove lines that are just whitespace or single punctuation
    lines = [ln for ln in lines if ln and len(ln) > 2]
    return "\n".join(lines)


def _extract_text_from_html(html: str, url: str) -> str:
    """Parse HTML → clean plaintext, removing navigational noise."""
    soup = BeautifulSoup(html, "lxml")

    # Remove noisy structural tags
    for selector in NOISE_TAGS:
        for tag in soup.select(selector):
            tag.decompose()

    # Prefer main content area; fall back to body
    content = None
    for selector in CONTENT_TAGS:
        content = soup.select_one(selector)
        if content:
            break
    if content is None:
        content = soup.find("body") or soup

    return _clean_text(content.get_text(separator="\n"))


def _same_domain(base_url: str, candidate: str) -> bool:
    """Return True if candidate shares the same hostname as base_url."""
    return urlparse(base_url).netloc == urlparse(candidate).netloc


def _collect_links(html: str, base_url: str) -> List[str]:
    """Extract in-domain <a href> links from an HTML page."""
    soup = BeautifulSoup(html, "lxml")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#")[0].split("?")[0]  # strip anchors / query
        full = urljoin(base_url, href)
        if _same_domain(base_url, full) and full not in links:
            links.append(full)
    return links


# ─── Main Loader ──────────────────────────────────────────────────────────────

def fetch_page(url: str) -> tuple[str, str] | tuple[None, None]:
    """
    Fetch a URL and return (html_text, resolved_url).
    Returns (None, None) on failure.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        # Only handle HTML pages
        ct = resp.headers.get("Content-Type", "")
        if "text/html" not in ct:
            return None, None
        return resp.text, resp.url
    except requests.RequestException as exc:
        console.print(f"  [yellow]⚠  Skip {url}: {exc}[/yellow]")
        return None, None


def load_documents_from_url(
    start_url: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    crawl: bool = True,
) -> List[Document]:
    """
    Load and chunk documentation starting from `start_url`.

    Parameters
    ----------
    start_url    : The root URL of the API documentation page.
    chunk_size   : Target character length per chunk.
    chunk_overlap: Overlap between consecutive chunks for context continuity.
    crawl        : If True, follow in-domain links up to MAX_PAGES.

    Returns
    -------
    List of LangChain Document objects ready for embedding.
    """
    visited: set[str] = set()
    queue: List[str] = [start_url]
    raw_docs: List[Document] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Fetching documentation pages…", total=None)

        while queue and len(visited) < MAX_PAGES:
            url = queue.pop(0)
            if url in visited:
                continue

            progress.update(task, description=f"[cyan]Fetching: {url[:80]}")
            html, resolved_url = fetch_page(url)
            if html is None:
                continue

            visited.add(resolved_url or url)
            text = _extract_text_from_html(html, resolved_url or url)

            if len(text) > 100:  # skip near-empty pages
                raw_docs.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": resolved_url or url,
                            "page_title": _extract_title(html),
                        },
                    )
                )
                console.print(
                    f"  [green]✓[/green] Loaded: {resolved_url or url} "
                    f"({len(text):,} chars)"
                )

            if crawl:
                new_links = _collect_links(html, resolved_url or url)
                for link in new_links:
                    if link not in visited and link not in queue:
                        queue.append(link)

            time.sleep(CRAWL_DELAY)

    console.print(
        f"\n[bold green]✔  Fetched {len(raw_docs)} page(s) "
        f"from {len(visited)} URL(s) visited.[/bold green]"
    )

    if not raw_docs:
        raise ValueError(
            f"No content could be extracted from {start_url}. "
            "Check that the URL is publicly accessible HTML."
        )

    # ── Chunk ────────────────────────────────────────────────
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(raw_docs)
    console.print(
        f"[bold cyan]✔  Split into {len(chunks)} chunks "
        f"(size≈{chunk_size}, overlap={chunk_overlap}).[/bold cyan]\n"
    )
    return chunks


def _extract_title(html: str) -> str:
    """Extract <title> text or return empty string."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("title")
    return tag.get_text().strip() if tag else ""
