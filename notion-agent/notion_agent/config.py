"""Configuration loaded from environment variables and .env files.

Keeps secrets out of source and gives us a single place to tune defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root if present. Does nothing if missing.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the agent.

    All values are resolved from environment variables with sensible defaults.
    """

    # --- Credentials ---
    anthropic_api_key: str
    notion_token: str

    # --- Models ---
    # Claude Opus 4.7 is Anthropic's most capable model as of April 2026.
    claude_model: str = "claude-opus-4-7"
    # Small, cheap, fast embedding model for semantic search over chunks.
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- Chunking ---
    # ~500 token chunks with 80 token overlap works well for retrieval.
    chunk_size_chars: int = 1800
    chunk_overlap_chars: int = 300

    # --- Retrieval ---
    top_k: int = 8

    # --- Agent loop ---
    max_agent_turns: int = 10
    max_tokens_per_turn: int = 4096

    # --- Storage ---
    index_dir: Path = Path.home() / ".notion_agent" / "index"

    @classmethod
    def from_env(cls) -> "Settings":
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        notion_token = os.getenv("NOTION_TOKEN", "").strip()

        if not anthropic_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your environment or a .env file."
            )
        if not notion_token:
            raise RuntimeError(
                "NOTION_TOKEN is not set. Create a Notion integration and export its token."
            )

        index_dir = Path(
            os.getenv("NOTION_AGENT_INDEX_DIR", str(Path.home() / ".notion_agent" / "index"))
        )
        index_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            anthropic_api_key=anthropic_key,
            notion_token=notion_token,
            claude_model=os.getenv("CLAUDE_MODEL", "claude-opus-4-7"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            index_dir=index_dir,
        )
