"""
Base agent class with shared Anthropic client and web search support.
"""

import os
import json
import time
import anthropic
from typing import Optional


class BaseAgent:
    """Base class for all agents providing shared client and helpers."""

    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4096

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.web_search_tool = {
            "type": "web_search_20250305",
            "name": "web_search",
        }

    def _call(
        self,
        system: str,
        messages: list,
        tools: Optional[list] = None,
        max_tokens: int = None,
        retries: int = 3,
    ) -> anthropic.types.Message:
        """Call the Anthropic API with automatic retry on rate limit errors."""
        kwargs = {
            "model": self.MODEL,
            "max_tokens": max_tokens or self.MAX_TOKENS,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        for attempt in range(retries):
            try:
                return self.client.messages.create(**kwargs)
            except anthropic.RateLimitError:
                wait = 60 * (attempt + 1)  # 60s, 120s, 180s
                print(f"\n  ⏳ Rate limit hit. Waiting {wait}s before retry ({attempt + 1}/{retries})...")
                time.sleep(wait)
                if attempt == retries - 1:
                    raise

    def _extract_text(self, response: anthropic.types.Message) -> str:
        """Extract all text content from a response."""
        parts = []
        for block in response.content:
            if block.type == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()

    def _extract_json(self, response: anthropic.types.Message) -> dict:
        """Extract and parse JSON from a response."""
        text = self._extract_text(response)
        # Strip markdown fences if present
        if "```" in text:
            lines = text.split("\n")
            json_lines = []
            inside = False
            for line in lines:
                if line.strip().startswith("```"):
                    inside = not inside
                    continue
                if inside or not any(
                    text.strip().startswith("```") for text in [line]
                ):
                    json_lines.append(line)
            text = "\n".join(json_lines)
        return json.loads(text.strip())
