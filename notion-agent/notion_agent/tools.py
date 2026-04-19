"""Tool definitions and dispatchers for the Claude agent loop.

Each tool is (a) a JSON schema that Claude sees in the `tools` parameter,
and (b) a Python function we run when Claude emits a `tool_use` block.

Keep the docstrings and descriptions crisp — Claude reads them to decide
which tool to call, so they should read like a short API doc.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable

from notion_client.errors import APIResponseError

from .notion_client_wrapper import NotionClientWrapper
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------- specs
# These are passed verbatim to the Anthropic API as the `tools` parameter.

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "read_page",
        "description": (
            "Read the full content of a single Notion page by its ID. "
            "Use this when the user references a specific page (via ID or URL) "
            "and you need its current contents before answering or editing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Notion page ID (with or without dashes) or full page URL.",
                },
            },
            "required": ["page_id"],
        },
    },
    {
        "name": "search_workspace",
        "description": (
            "Semantic search across the local vector index of the user's Notion workspace. "
            "Returns the top matching chunks with page titles, IDs, URLs, and similarity scores. "
            "Prefer this over Notion's native search for anything that requires conceptual "
            "matching (e.g. 'risks for Project Phoenix', 'prompt engineering principles'). "
            "Run multiple searches with different queries when a question spans topics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language search query.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks to return. Default 8, max 20.",
                    "default": 8,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "append_section",
        "description": (
            "Append a new section (H2 heading plus optional paragraph body) to "
            "the end of a Notion page. Use this for write operations like "
            "'add a Next Steps section' or 'append a summary of our discussion'. "
            "Always confirm the target page_id and the content before calling."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Notion page ID or URL to append to.",
                },
                "heading": {
                    "type": "string",
                    "description": "Heading text for the new section (rendered as H2).",
                },
                "body": {
                    "type": "string",
                    "description": (
                        "Optional body paragraph(s) under the heading. "
                        "Use plain text; long bodies will be split across multiple paragraph blocks."
                    ),
                },
            },
            "required": ["page_id", "heading"],
        },
    },
]


# ---------------------------------------------------------------- dispatchers


class ToolRunner:
    """Dispatches tool calls from Claude to actual implementations."""

    def __init__(self, notion: NotionClientWrapper, store: VectorStore, top_k: int = 8) -> None:
        self.notion = notion
        self.store = store
        self.default_top_k = top_k
        self._dispatch: dict[str, Callable[[dict[str, Any]], Any]] = {
            "read_page": self._read_page,
            "search_workspace": self._search_workspace,
            "append_section": self._append_section,
        }

    def run(self, name: str, tool_input: dict[str, Any]) -> str:
        """Execute a tool and return its output as a string.

        Claude's tool-use protocol expects the `content` of a tool_result
        block to be a string (or a list of content blocks). We stringify
        JSON responses so everything is structured but uniform.
        """
        handler = self._dispatch.get(name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            result = handler(tool_input)
            return json.dumps(result, ensure_ascii=False)
        except APIResponseError as e:
            logger.warning("Notion API error in %s: %s", name, e)
            return json.dumps({"error": f"Notion API error: {e.code}", "message": str(e)})
        except Exception as e:
            logger.exception("Unhandled error in tool %s", name)
            return json.dumps({"error": type(e).__name__, "message": str(e)})

    # ---------------------------------------------------------- impls

    def _read_page(self, inp: dict[str, Any]) -> dict[str, Any]:
        page_id = inp["page_id"]
        page = self.notion.get_page(page_id)
        # Cap text we return to the model — 20k chars is ~5k tokens, plenty
        # for a page summary and keeps us honest about context cost.
        text = page.text
        truncated = False
        if len(text) > 20_000:
            text = text[:20_000]
            truncated = True
        return {
            "page_id": page.page_id,
            "title": page.title,
            "url": page.url,
            "text": text,
            "truncated": truncated,
        }

    def _search_workspace(self, inp: dict[str, Any]) -> dict[str, Any]:
        query = inp["query"]
        top_k = min(int(inp.get("top_k", self.default_top_k)), 20)
        results = self.store.search(query, top_k=top_k)
        if not results:
            return {
                "query": query,
                "results": [],
                "note": "Vector index is empty. Run `notion-agent index` first to build it.",
            }
        return {
            "query": query,
            "results": self.store.to_jsonable(results),
        }

    def _append_section(self, inp: dict[str, Any]) -> dict[str, Any]:
        page_id = inp["page_id"]
        heading = inp["heading"]
        body = inp.get("body")
        self.notion.append_section(page_id=page_id, heading=heading, body=body)
        return {
            "status": "ok",
            "page_id": page_id,
            "heading": heading,
            "body_chars": len(body) if body else 0,
        }
