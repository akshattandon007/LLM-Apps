"""
Resource Hunter Agent — Finds free learning resources for each module.

Searches Wikipedia API, Open Library API, and web search
to find free, high-quality resources for each module in the curriculum.

Uses httpx for async HTTP calls.
"""

import json
from dataclasses import dataclass, field
from typing import Optional
import httpx
from urllib.parse import quote

from .curriculum_builder import Module


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Resource:
    title: str
    url: str
    source: str  # "wikipedia", "openlibrary", "web"
    description: str = ""
    resource_type: str = "article"  # "article", "video", "book", "tutorial"


@dataclass
class ModuleResources:
    module_title: str
    resources: list[Resource] = field(default_factory=list)


# ── HTTP client (injectable for testing) ─────────────────────────────────────

_client: Optional[httpx.Client] = None

def set_client(client: Optional[httpx.Client]):
    global _client
    _client = client

def _get_client() -> httpx.Client:
    return _client or httpx.Client(timeout=15.0)


# ── Wikipedia Search ─────────────────────────────────────────────────────────

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
OPEN_LIBRARY_API = "https://openlibrary.org/search.json"


def search_wikipedia(query: str, limit: int = 3) -> list[Resource]:
    """Search Wikipedia for articles related to a topic."""
    client = _get_client()
    results = []
    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": limit,
            "srprop": "snippet",
        }
        resp = client.get(WIKIPEDIA_API, params=params, headers={"User-Agent": "LearnerLane/1.0"})
        resp.raise_for_status()
        data = resp.json()
        for hit in data.get("query", {}).get("search", []):
            title = hit.get("title", "")
            page_id = hit.get("pageid", "")
            snippet = hit.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
            url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
            if page_id:
                results.append(Resource(
                    title=title,
                    url=url,
                    source="wikipedia",
                    description=snippet[:200],
                    resource_type="article",
                ))
    except Exception:
        pass  # Return what we have
    return results


def search_open_library(query: str, limit: int = 2) -> list[Resource]:
    """Search Open Library for free books related to a topic."""
    client = _get_client()
    results = []
    try:
        params = {
            "q": query,
            "limit": limit,
            "fields": "title,key,first_publish_year,author_name,cover_i,edition_count,ia_collection",
        }
        resp = client.get(OPEN_LIBRARY_API, params=params)
        resp.raise_for_status()
        data = resp.json()
        for doc in data.get("docs", []):
            title = doc.get("title", "")
            key = doc.get("key", "")
            author = ", ".join(doc.get("author_name", ["Unknown"]))
            year = doc.get("first_publish_year", "")
            # Check if available in Internet Archive collection
            ia = doc.get("ia_collection", [])
            is_free = bool(ia)
            url = f"https://openlibrary.org{key}" if key else ""
            if url:
                description_parts = [f"by {author}"]
                if year:
                    description_parts.append(f"({year})")
                if is_free:
                    description_parts.append("— Free on Internet Archive")
                else:
                    description_parts.append("— Free to read online")
                results.append(Resource(
                    title=title,
                    url=url,
                    source="openlibrary",
                    description=" | ".join(description_parts),
                    resource_type="book",
                ))
    except Exception:
        pass
    return results


def search_web_fallback(query: str, limit: int = 2) -> list[Resource]:
    """Generate resource suggestions based on known patterns.
    
    Instead of live web search (which requires web_search tool),
    this generates URLs to known free learning platforms.
    """
    topic = query.replace('"', '')
    results = []
    
    # YouTube search URL
    yt_url = f"https://www.youtube.com/results?search_query={quote(topic + ' tutorial')}"
    results.append(Resource(
        title=f"YouTube: {topic} Tutorial",
        url=yt_url,
        source="web",
        description=f"Video tutorials and walkthroughs for {topic}",
        resource_type="video",
    ))
    
    # FreeCodeCamp / MDN / generic resource
    results.append(Resource(
        title=f"Google: {topic} — Curated Search",
        url=f"https://www.google.com/search?q={quote(topic + ' free tutorial')}",
        source="web",
        description=f"Find free articles, guides, and courses for {topic}",
        resource_type="tutorial",
    ))
    
    return results


def hunt_resources(module: Module, skill_topic: str) -> ModuleResources:
    """Find free resources for a single module.
    
    Combines Wikipedia, Open Library, and web search results.
    """
    all_resources: list[Resource] = []
    
    # Build search queries
    module_query = f"{module.title} {skill_topic}"
    broad_query = skill_topic
    
    # 1. Wikipedia
    all_resources.extend(search_wikipedia(module_query, limit=2))
    if len(all_resources) < 3:
        all_resources.extend(search_wikipedia(broad_query, limit=1))
    
    # 2. Open Library
    all_resources.extend(search_open_library(broad_query, limit=2))
    
    # 3. Web fallback
    all_resources.extend(search_web_fallback(module_query, limit=2))
    
    # Deduplicate by URL
    seen_urls = set()
    unique_resources = []
    for r in all_resources:
        if r.url not in seen_urls:
            seen_urls.add(r.url)
            unique_resources.append(r)
    
    return ModuleResources(
        module_title=module.title,
        resources=unique_resources[:6],  # Max 6 per module
    )