"""
HN Fetcher — fetch stories and comments from Hacker News via Algolia API.

Uses the official HN Algolia Search API (no API key required).
Rate limit: ~10,000 requests/hour — generous for our use case.
"""

import requests
import time
from typing import Any

ALGOLIA_URL = "https://hn.algolia.com/api/v1"


def search_stories(topic: str, limit: int = 30) -> list[dict[str, Any]]:
    """Search HN stories by topic, returns list of story dicts.

    Uses Algolia's search endpoint with:
    - tags=story to get only story items
    - hitsPerPage=limit
    - sorted by points (relevance × popularity)
    """
    url = f"{ALGOLIA_URL}/search"
    params = {
        "query": topic,
        "tags": "story",
        "hitsPerPage": min(limit, 200),
        "advancedSyntax": True,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    hits = data.get("hits", [])
    return hits


def fetch_comments_for_story(story_object_id: str, max_comments: int = 20) -> list[dict[str, Any]]:
    """Fetch top comments for a given story/story object ID.

    Uses Algolia search with tags=comment and numericFilters on story objectID.
    Returns sorted by points descending.
    """
    url = f"{ALGOLIA_URL}/search"
    params = {
        "tags": f"comment,story_{story_object_id}",
        "hitsPerPage": min(max_comments, 100),
        "numericFilters": "points>0",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("hits", [])


def fetch_story_comments_batch(
    topic: str,
    story_limit: int = 30,
    comments_per_story: int = 10,
) -> list[dict[str, Any]]:
    """Full pipeline: search stories → fetch comments → return document chunks.

    Each returned dict has:
      - text: the content text (story title + URL or comment text)
      - source: "story" or "comment"
      - story_title: parent story title
      - hn_url: direct link to item
      - points: upvotes
      - author: username
      - created_at: ISO timestamp
    """
    stories = search_stories(topic, limit=story_limit)
    documents = []

    for story in stories:
        title = story.get("title", "")
        url = story.get("url", "")
        story_id = story.get("objectID", "")
        points = story.get("points", 0) or 0
        author = story.get("author", "unknown")
        created = story.get("created_at", "")

        if title and points > 0:
            documents.append({
                "text": f"{title}\n\n{url}" if url else title,
                "source": "story",
                "story_title": title,
                "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
                "points": points,
                "author": author,
                "created_at": created,
            })

        # Fetch top comments
        comments = fetch_comments_for_story(story_id, max_comments=comments_per_story)
        for comment in comments:
            comment_text = comment.get("comment_text", "")
            if not comment_text:
                continue
            # Strip HTML tags from comment text (Algolia returns HTML)
            comment_text = comment_text.replace("<p>", "\n\n").replace("</p>", "")
            comment_text = comment_text.replace("<i>", "*").replace("</i>", "*")
            comment_text = comment_text.replace("<b>", "**").replace("</b>", "**")
            comment_text = comment_text.replace("<code>", "`").replace("</code>", "`")
            comment_text = comment_text.replace("<pre>", "").replace("</pre>", "")
            comment_text = comment_text.replace("<a href=\"", "").replace("\" rel=\"nofollow\">", " ")
            comment_text = comment_text.replace("</a>", "")

            comment_points = comment.get("points", 0) or 0
            if comment_points < 1:
                continue  # Skip low-value comments

            documents.append({
                "text": comment_text.strip(),
                "source": "comment",
                "story_title": title,
                "hn_url": f"https://news.ycombinator.com/item?id={comment.get('objectID', '')}",
                "points": comment_points,
                "author": comment.get("author", "unknown"),
                "created_at": comment.get("created_at", created),
            })

        # Be nice to the API
        time.sleep(0.3)

    return documents
