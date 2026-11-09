"""Base agent class that all TeamScribe agents extend."""

from __future__ import annotations

import os
from typing import Optional


class BaseAgent:
    """Base class for a TeamScribe agent with LLM access.

    Each agent has a name, role description, and can call an LLM
    with structured system + user prompts.

    The OpenAI client is lazy-initialized on first call_llm() so that
    unit tests can mock call_llm() without needing real credentials.
    """

    def __init__(
        self,
        name: str,
        role: str,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.name = name
        self.role = role
        self.model = model or os.getenv("TEAMSCRIBE_MODEL", "gpt-4o-mini")
        self._api_key = api_key
        self._base_url = base_url
        self._client = None  # lazy-initialized

    @property
    def client(self):
        """Lazy OpenAI client — created on first access."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self._api_key or os.getenv("OPENAI_API_KEY", ""),
                base_url=self._base_url or os.getenv("OPENAI_BASE_URL", None),
            )
        return self._client

    def call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Send a prompt to the LLM and return the text response."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def system_prompt(self) -> str:
        """Override in subclasses to provide the agent-specific system prompt."""
        return f"You are {self.name}, {self.role}. Respond concisely and accurately."