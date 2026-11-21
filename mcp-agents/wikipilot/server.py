"""WikiPilot — Wikipedia MCP server.

Provides MCP tools for Wikipedia knowledge retrieval using the free,
zero-auth Wikipedia REST API (en.wikipedia.org/api/rest_v1).

Run:
    python -m mcp run server.py
    # or
    uv run --with mcp python -m mcp run server.py
"""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from wikipilot_client import (
    ArticleNotFound,
    WikipediaError,
    search_articles,
    get_summary,
    get_article,
    get_random_article,
    on_this_day,
    get_related_articles,
    get_article_categories,
)

mcp = FastMCP(
    "WikiPilot",
    instructions=(
        "Wikipedia knowledge MCP server. Search articles, get summaries and full content, "
        "discover random pages, find on-this-day historical events, and explore related "
        "articles — all via the free Wikipedia API. No API key required."
    ),
)


# ── Tools ──────────────────────────────────────────────────────────────────


@mcp.tool()
def search_wikipedia(query: str, limit: int = 10) -> str:
    """Search Wikipedia articles by keyword. Returns matching titles, snippets, and URLs.

    Args:
        query: Search query (free text, e.g. 'quantum physics' or 'Eiffel Tower').
        limit: Maximum results to return (1-50, default 10).
    """
    try:
        results = search_articles(query, limit=limit)
    except WikipediaError as exc:
        return f"Wikipedia API error: {exc}"

    if not results:
        return f"No articles found for '{query}'."

    lines = [f"📚 Search results for **{query}**"]
    for i, r in enumerate(results, 1):
        snippet = r["snippet"][:200]
        lines.append(f"\n{i}. **{r['title']}**")
        lines.append(f"   _{snippet}..._")
        lines.append(f"   🔗 {r['url']}")
    return "\n".join(lines)


@mcp.tool()
def summarize_article(title: str) -> str:
    """Get a concise summary (first paragraph + thumbnail URL) for a Wikipedia article.

    Args:
        title: Article title (case-sensitive, e.g. 'Python (programming language)').
    """
    try:
        info = get_summary(title)
    except ArticleNotFound:
        return f"❌ Article not found: '{title}'. Try searching with `search_wikipedia` first."
    except WikipediaError as exc:
        return f"Wikipedia API error: {exc}"

    lines = [f"## {info['title']}"]
    if info["thumbnail_url"]:
        lines.append(f"![]({info['thumbnail_url']})")
    extract = info["extract"][:2000]
    lines.append(f"\n{extract}")
    lines.append(f"\n🔗 [Read on Wikipedia]({info['url']})")
    return "\n".join(lines)


@mcp.tool()
def read_article(title: str) -> str:
    """Get the full text content of a Wikipedia article. Use when the summary isn't enough.

    Args:
        title: Article title (case-sensitive).
    """
    try:
        info = get_article(title)
    except ArticleNotFound:
        return f"❌ Article not found: '{title}'."
    except WikipediaError as exc:
        return f"Wikipedia API error: {exc}"

    content = info.get("content", info.get("extract", ""))

    # Truncate to prevent context overflow
    if len(content) > 25_000:
        content = content[:25_000] + "\n\n[... article truncated at 25K characters ...]"

    return f"# {info['title']}\n\n{content}\n\n🔗 {info['url']}"


@mcp.tool()
def random_article() -> str:
    """Fetch a random Wikipedia article summary. Great for serendipitous discovery."""
    try:
        info = get_random_article()
    except WikipediaError as exc:
        return f"Wikipedia API error: {exc}"

    lines = [f"## 🎲 Random article: {info['title']}"]
    if info["thumbnail_url"]:
        lines.append(f"![]({info['thumbnail_url']})")
    extract = info["extract"][:2000]
    lines.append(f"\n{extract}")
    lines.append(f"\n🔗 [Read on Wikipedia]({info['url']})")
    return "\n".join(lines)


@mcp.tool()
def today_in_history(month: Optional[int] = None, day: Optional[int] = None) -> str:
    """Get historical events that happened on a specific date. Defaults to today (UTC).

    Args:
        month: Month number (1-12). Leave blank for today.
        day: Day of month (1-31). Leave blank for today.
    """
    try:
        events = on_this_day(month=month, day=day)
    except WikipediaError as exc:
        return f"Wikipedia API error: {exc}"

    if not events:
        m = month or "?"
        d = day or "?"
        return f"No events found for {m}/{d}."

    lines = [f"## 📜 On this day ({month or 'today'}/{day or 'today'})"]
    for i, ev in enumerate(events[:20], 1):
        lines.append(f"\n{i}. **{ev['year']}** — {ev['description'][:300]}")
        if ev['url']:
            lines.append(f"   🔗 {ev['url']}")
    if len(events) > 20:
        lines.append(f"\n... and {len(events) - 20} more events.")
    return "\n".join(lines)


@mcp.tool()
def related_articles(title: str, limit: int = 5) -> str:
    """Find articles related to a given Wikipedia article.

    Args:
        title: Article title to find related pages for.
        limit: Maximum related articles to return (default 5).
    """
    try:
        items = get_related_articles(title, limit=limit)
    except ArticleNotFound:
        return f"❌ Article not found: '{title}'."
    except WikipediaError as exc:
        return f"Wikipedia API error: {exc}"

    if not items:
        return f"No related articles found for '{title}'."

    lines = [f"## 🔗 Related to **{title}**"]
    for i, item in enumerate(items, 1):
        lines.append(f"\n{i}. **{item['title']}**")
        lines.append(f"   🔗 {item['url']}")
    return "\n".join(lines)


@mcp.tool()
def article_categories(title: str) -> str:
    """List the Wikipedia categories an article belongs to.

    Args:
        title: Article title.
    """
    try:
        cats = get_article_categories(title)
    except ArticleNotFound:
        return f"❌ Article not found: '{title}'."
    except WikipediaError as exc:
        return f"Wikipedia API error: {exc}"

    if not cats:
        return f"No categories found for '{title}'."

    lines = [f"## 🏷️ Categories for **{title}**"]
    for i, cat in enumerate(cats, 1):
        lines.append(f"{i}. {cat}")
    return "\n".join(lines)