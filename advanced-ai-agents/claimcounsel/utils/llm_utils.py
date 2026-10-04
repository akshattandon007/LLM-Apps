"""
LLM interaction utilities for ClaimCounsel agents.
Provides a simple interface to call LLMs for text generation, analysis, and extraction.
Client is initialized lazily to avoid credential checks on module import.
"""

import json
import os
from typing import Optional

from config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_MAX_TOKENS, LLM_TEMPERATURE


def _has_credentials() -> bool:
    """Check if LLM credentials are available (API key or env var)."""
    if LLM_API_KEY:
        return True
    if os.environ.get("OPENAI_API_KEY"):
        return True
    return False


class LLMClient:
    """Lightweight LLM client wrapping an OpenAI-compatible API.
    Client is created lazily on first use to avoid credential enforcement."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or LLM_API_KEY
        self.model = model or LLM_MODEL
        self.base_url = base_url or LLM_BASE_URL
        self._client = None

    def _get_client(self):
        """Lazy init of the OpenAI client — only when we actually need to call the API."""
        if self._client is None:
            from openai import OpenAI
            key = self.api_key or os.environ.get("OPENAI_API_KEY", "")
            self._client = OpenAI(api_key=key, base_url=self.base_url)
        return self._client

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        output_json: bool = False,
    ) -> str:
        """
        Send a chat completion request.

        Args:
            system_prompt: System-level instruction for the model.
            user_prompt: The user's message / input data.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            output_json: If True, requests structured JSON output.

        Returns:
            The model's response text.
        """
        if not _has_credentials():
            return "[LLM unavailable: No API key configured. Set LLM_API_KEY or OPENAI_API_KEY.]"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or LLM_TEMPERATURE,
            "max_tokens": max_tokens or LLM_MAX_TOKENS,
        }

        if output_json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            client = self._get_client()
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[LLM Error: {e}]"

    def extract_json(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Send a request and parse the response as JSON.
        Returns a dict on success, or an error dict on failure.
        """
        raw = self.chat(system_prompt, user_prompt, output_json=True)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"error": "Failed to parse JSON from LLM response", "raw": str(raw)}


# Singleton
_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the default LLM client singleton."""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client