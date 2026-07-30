"""Configuration helpers.

Reads from environment variables, with optional support for a local ``.env``
file if ``python-dotenv`` is installed. Nothing here is required for the
offline demo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass  # dotenv is optional


@dataclass
class Settings:
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-haiku-latest"
    football_data_api_key: Optional[str] = None

    @classmethod
    def load(cls) -> "Settings":
        _load_dotenv()
        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
            anthropic_model=os.environ.get(
                "ANTHROPIC_MODEL", "claude-3-5-haiku-latest"
            ),
            football_data_api_key=os.environ.get("FOOTBALL_DATA_API_KEY"),
        )

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)
