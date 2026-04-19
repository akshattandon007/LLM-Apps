"""Thin wrapper around the official Notion SDK.

Notion's API returns deeply nested block trees with a lot of ceremony.
This module flattens that into simple primitives the rest of the agent can use:

- `get_page(page_id)` → title + flat markdown-ish text
- `walk_workspace()`  → iterator over every page the integration can see
- `append_markdown(page_id, text)` → append a heading + paragraph section
- `search(query)`    → Notion's native keyword search, used as a fallback/seed

We deliberately keep the surface small. Anything Notion-specific and weird
(rich text arrays, block type discriminators, pagination cursors) lives here
so the agent layer stays clean.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Iterator

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)

# Block types whose `rich_text` we extract as plain text.
# Everything else (dividers, images, etc.) becomes a short marker or is skipped.
_TEXT_BLOCK_TYPES = {
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "to_do",
    "toggle",
    "quote",
    "callout",
    "code",
}


@dataclass
class NotionPage:
    """Flat representation of a Notion page's content."""

    page_id: str
    title: str
    url: str
    text: str
    # Block-level breakdown lets us attribute chunks back to specific blocks later.
    blocks: list[dict[str, Any]] = field(default_factory=list)


def _normalise_id(page_id: str) -> str:
    """Accept page IDs with or without dashes, or a full Notion URL.

    Notion URLs place the page ID as the final 32-hex segment of the path,
    e.g. `.../My-Page-abcdef0123456789abcdef0123456789`. We anchor the match
    to the end of the string so a page title that happens to contain hex
    characters can't be mistaken for the ID.
    """
    collapsed = page_id.replace("-", "")
    # Prefer the trailing 32-hex block — this is where Notion always puts it.
    match = re.search(r"([0-9a-fA-F]{32})$", collapsed)
    if not match:
        # Fallback: any 32-hex run anywhere. Handles exotic inputs.
        match = re.search(r"([0-9a-fA-F]{32})", collapsed)
    if not match:
        # Let the API complain with its own error if this is actually wrong.
        return page_id
    raw = match.group(1).lower()
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def _rich_text_to_plain(rich_text: list[dict[str, Any]]) -> str:
    """Flatten Notion's rich text array into a plain string."""
    return "".join(rt.get("plain_text", "") for rt in rich_text)


def _block_to_text(block: dict[str, Any]) -> str:
    """Render a single block to a markdown-ish line of text."""
    btype = block.get("type")
    if btype not in _TEXT_BLOCK_TYPES:
        return ""
    payload = block.get(btype, {})
    text = _rich_text_to_plain(payload.get("rich_text", []))
    if not text:
        return ""

    # Light markdown-flavoured prefixes so downstream chunking preserves structure.
    if btype == "heading_1":
        return f"# {text}"
    if btype == "heading_2":
        return f"## {text}"
    if btype == "heading_3":
        return f"### {text}"
    if btype == "bulleted_list_item":
        return f"- {text}"
    if btype == "numbered_list_item":
        return f"1. {text}"
    if btype == "to_do":
        checked = payload.get("checked", False)
        return f"- [{'x' if checked else ' '}] {text}"
    if btype == "quote":
        return f"> {text}"
    if btype == "code":
        lang = payload.get("language", "")
        return f"```{lang}\n{text}\n```"
    return text


class NotionClientWrapper:
    """Small, opinionated facade over notion-client."""

    def __init__(self, token: str) -> None:
        self._client = Client(auth=token)

    # ------------------------------------------------------------------ reads

    def get_page(self, page_id: str) -> NotionPage:
        """Return a page's title, URL, and flattened text content."""
        pid = _normalise_id(page_id)
        page_obj = self._client.pages.retrieve(page_id=pid)
        title = self._extract_title(page_obj)
        url = page_obj.get("url", "")

        blocks = list(self._iter_blocks(pid))
        lines = [_block_to_text(b) for b in blocks]
        text = "\n".join(line for line in lines if line)

        return NotionPage(
            page_id=pid,
            title=title,
            url=url,
            text=text,
            blocks=blocks,
        )

    def _iter_blocks(self, block_id: str, depth: int = 0, max_depth: int = 3) -> Iterator[dict[str, Any]]:
        """Recursively yield every block beneath `block_id` (depth-first).

        We cap depth to keep pathological nesting from blowing up the crawler.
        Most real Notion pages are only 2-3 levels deep.
        """
        if depth > max_depth:
            return

        cursor: str | None = None
        while True:
            try:
                response = self._client.blocks.children.list(
                    block_id=block_id,
                    start_cursor=cursor,
                )
            except APIResponseError as e:
                logger.warning("Failed to list children of %s: %s", block_id, e)
                return

            for block in response.get("results", []):
                yield block
                if block.get("has_children"):
                    yield from self._iter_blocks(block["id"], depth + 1, max_depth)

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

    def walk_workspace(self) -> Iterator[NotionPage]:
        """Yield every page the integration has access to.

        Uses Notion's /search endpoint with no query, filtered to pages only.
        This is the canonical way for an integration to enumerate its scope.
        """
        cursor: str | None = None
        seen: set[str] = set()
        while True:
            response = self._client.search(
                query="",
                filter={"property": "object", "value": "page"},
                start_cursor=cursor,
            )
            for result in response.get("results", []):
                pid = result.get("id")
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                try:
                    yield self.get_page(pid)
                except APIResponseError as e:
                    logger.warning("Skipping page %s: %s", pid, e)
                    continue

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

    def search(self, query: str, page_size: int = 20) -> list[dict[str, Any]]:
        """Run Notion's native full-text search.

        Useful as a fallback — and as a seed during initial crawls — but it's
        exactly the feature users complain about, which is why we layer a
        vector index on top of it.
        """
        response = self._client.search(
            query=query,
            filter={"property": "object", "value": "page"},
            page_size=page_size,
        )
        hits: list[dict[str, Any]] = []
        for result in response.get("results", []):
            hits.append({
                "page_id": result.get("id", ""),
                "title": self._extract_title(result),
                "url": result.get("url", ""),
            })
        return hits

    # ----------------------------------------------------------------- writes

    def append_section(
        self,
        page_id: str,
        heading: str,
        body: str | None = None,
    ) -> dict[str, Any]:
        """Append an H2 heading and optional paragraph body to a page.

        Chosen deliberately over a raw "append markdown" API because it gives
        the agent a predictable, audit-friendly write primitive.
        """
        pid = _normalise_id(page_id)
        children: list[dict[str, Any]] = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": heading}}]
                },
            }
        ]
        if body:
            # Split long bodies across multiple paragraph blocks — Notion caps
            # a single rich_text content at 2000 chars.
            for chunk in _split_for_notion(body, limit=1900):
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    },
                })
        return self._client.blocks.children.append(block_id=pid, children=children)

    # ---------------------------------------------------------------- helpers

    @staticmethod
    def _extract_title(page_obj: dict[str, Any]) -> str:
        """Notion pages can store their title in several places depending on
        whether they're workspace pages or database rows."""
        props = page_obj.get("properties", {})
        # Most pages have a "title" property.
        for prop in props.values():
            if prop.get("type") == "title":
                return _rich_text_to_plain(prop.get("title", [])) or "(untitled)"
        # Some objects carry it at the top level.
        if "title" in page_obj:
            return _rich_text_to_plain(page_obj["title"]) or "(untitled)"
        return "(untitled)"


def _split_for_notion(text: str, limit: int = 1900) -> list[str]:
    """Split `text` into chunks that fit Notion's per-block content cap."""
    if len(text) <= limit:
        return [text]
    out: list[str] = []
    buf = ""
    for para in text.split("\n"):
        if len(buf) + len(para) + 1 > limit:
            if buf:
                out.append(buf)
            # Handle paragraphs that are themselves too long.
            while len(para) > limit:
                out.append(para[:limit])
                para = para[limit:]
            buf = para
        else:
            buf = f"{buf}\n{para}" if buf else para
    if buf:
        out.append(buf)
    return out
