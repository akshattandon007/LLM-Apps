"""Story generation engine — talks to any OpenAI-compatible LLM API."""

from __future__ import annotations

import json
import os
import sys
from typing import Optional

import requests

from .models import StoryNode, Choice, StorySession
from .prompts import (
    SYSTEM_PROMPT,
    FIRST_CHAPTER_PROMPT,
    NEXT_CHAPTER_PROMPT,
    SUMMARY_PROMPT,
)


def _build_narration_history(session: StorySession, max_chars: int = 3000) -> str:
    """Build a compact history of past narrative for the next-chapter prompt."""
    parts = []
    char_count = 0
    # Go through nodes from newest to oldest, stop when we have enough context
    for node in reversed(session.nodes):
        entry = f"--- Chapter (node {node.id}) ---\n{node.narrative[:500]}"
        if char_count + len(entry) > max_chars:
            break
        parts.insert(0, entry)
        char_count += len(entry)
    return "\n\n".join(parts)


class StoryEngine:
    """Generates story chapters via an OpenAI-compatible chat API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: str = "https://openrouter.ai/api/v1",
        model: str = "openai/gpt-4o-mini",
        max_tokens: int = 2048,
        temperature: float = 0.9,
    ):
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        if not self.api_key:
            print(
                "ERROR: No LLM API key found. Set LLM_API_KEY environment variable "
                "or pass api_key to StoryEngine().",
                file=sys.stderr,
            )
            sys.exit(1)

    def _call_api(self, messages: list[dict]) -> dict:
        """Make a chat completion request and return the parsed JSON response."""
        resp = requests.post(
            f"{self.api_base}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/akshattandon007/LLM-Apps",
                "X-Title": "StoryWeaver",
            },
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # Parse: try direct JSON first, then strip markdown fences
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                cleaned = cleaned.rsplit("```", 1)[0].strip()
            return json.loads(cleaned)

    def generate_first_chapter(
        self, session: StorySession, next_node_id: int = 1
    ) -> StoryNode:
        """Generate the opening chapter of a new story."""
        user_prompt = FIRST_CHAPTER_PROMPT.format(
            title=session.title,
            genre=session.genre,
            setting=session.setting,
            characters=session.characters,
            premise=session.premise,
        )

        result = self._call_api(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )

        narrative = result.get("narrative", "")
        choices_raw = result.get("choices", [])

        choices = []
        for i, c in enumerate(choices_raw):
            choices.append(
                Choice(
                    text=c.get("text", f"Option {i+1}"),
                    next_node_id=c.get("next_node_id", next_node_id + i + 1),
                )
            )

        return StoryNode(id=next_node_id, narrative=narrative, choices=choices)

    def generate_next_chapter(
        self, session: StorySession, chosen_text: str
    ) -> StoryNode:
        """Generate the next chapter following the reader's last choice."""
        history = _build_narration_history(session)
        next_id = max((n.id for n in session.nodes), default=0) + 1

        user_prompt = NEXT_CHAPTER_PROMPT.format(
            title=session.title,
            genre=session.genre,
            narration_history=history,
            chosen_text=chosen_text,
        )

        result = self._call_api(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )

        narrative = result.get("narrative", "")
        choices_raw = result.get("choices", [])

        choices = []
        for i, c in enumerate(choices_raw):
            next_node = c.get("next_node_id", next_id + i + 1)
            choices.append(
                Choice(
                    text=c.get("text", f"Option {i+1}"),
                    next_node_id=next_node,
                )
            )

        return StoryNode(id=next_id, narrative=narrative, choices=choices)

    def generate_epilogue(self, session: StorySession) -> str:
        """Generate a closing epilogue for a finished story."""
        user_prompt = SUMMARY_PROMPT.format(
            title=session.title,
            genre=session.genre,
            chapter_count=len(session.nodes),
        )

        resp = requests.post(
            f"{self.api_base}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/akshattandon007/LLM-Apps",
                "X-Title": "StoryWeaver",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 512,
                "temperature": 0.8,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
