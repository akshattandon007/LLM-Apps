"""ClipRef — utility functions: file I/O, config, hashing, embedding model loading."""

from __future__ import annotations

import hashlib
import os
import re
import time
import datetime
from pathlib import Path

from clipref.models import (
    _DEFAULT_EMBEDDING_MODEL,
    _DEFAULT_BASE_URL,
    _DEFAULT_CHUNK_SIZE,
    _DEFAULT_CHUNK_OVERLAP,
    _DEFAULT_TOP_K,
    _DEFAULT_LLM_MODEL,
    _COLLECTION_NAME,
)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def get_env(key: str, default: str = "") -> str:
    """Read an env var, falling back to a .clipref.env file."""
    val = os.environ.get(key)
    if val:
        return val
    # Check .clipref.env files (first found wins)
    for candidate in [
        Path.home() / ".clipref.env",
        Path.cwd() / ".clipref.env",
    ]:
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#") or "=" not in stripped:
                        continue
                    k, _, v = stripped.partition("=")
                    if k.strip() == key:
                        return v.strip().strip("\"'")
            except OSError:
                continue
    return default


def embedding_model_name() -> str:
    return get_env("CLIPREF_MODEL", _DEFAULT_EMBEDDING_MODEL)


def chunk_size() -> int:
    return int(get_env("CLIPREF_CHUNK_SIZE", str(_DEFAULT_CHUNK_SIZE)))


def chunk_overlap() -> int:
    return int(get_env("CLIPREF_CHUNK_OVERLAP", str(_DEFAULT_CHUNK_OVERLAP)))


def top_k() -> int:
    return int(get_env("CLIPREF_TOP_K", str(_DEFAULT_TOP_K)))


def llm_model() -> str:
    return get_env("CLIPREF_LLM_MODEL", _DEFAULT_LLM_MODEL)


def llm_base_url() -> str:
    return get_env("OPENAI_BASE_URL", _DEFAULT_BASE_URL)


def llm_api_key() -> str | None:
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or ""
    if key:
        return key
    # Try .clipref.env
    return get_env("OPENAI_API_KEY") or get_env("OPENROUTER_API_KEY") or None


def resolve_db_path(db_arg: str | None) -> Path:
    """Resolve the ChromaDB persistence directory."""
    if db_arg:
        return Path(db_arg).expanduser().resolve()
    env_db = get_env("CLIPREF_DB_DIR")
    if env_db:
        return Path(env_db).expanduser().resolve()
    return Path.home() / ".clipref"


def collection_name() -> str:
    return _COLLECTION_NAME


# ---------------------------------------------------------------------------
# Embedding model singleton
# ---------------------------------------------------------------------------

_EMBEDDING_MODEL = None


def get_embedding_model(model_name: str | None = None):
    """Load a sentence-transformers model (cached singleton)."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL
    from sentence_transformers import SentenceTransformer

    name = model_name or embedding_model_name()
    _EMBEDDING_MODEL = SentenceTransformer(name)
    return _EMBEDDING_MODEL


# ---------------------------------------------------------------------------
# File hashing
# ---------------------------------------------------------------------------

def hash_file(path: Path) -> str:
    """SHA-256 of a file's content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_path(path: Path) -> str:
    """Deterministic ID from file path + modification time for idempotent indexing."""
    try:
        mtime = str(int(path.stat().st_mtime))
    except OSError:
        mtime = "0"
    raw = f"{path.resolve()}::{mtime}"
    return hashlib.sha256(raw.encode()).hexdigest()


def chunk_id(source_path: Path, chunk_index: int, file_hash: str) -> str:
    """Deterministic chunk ID."""
    raw = f"{source_path.resolve()}::{file_hash}::chunk_{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------

_BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".gz", ".tar", ".7z", ".rar",
    ".mp3", ".wav", ".ogg", ".flac",
    ".mp4", ".avi", ".mov", ".mkv",
    ".exe", ".bin", ".dll", ".so", ".dylib",
    ".o", ".a", ".lib",
    ".pyc", ".pyd", ".egg", ".whl",
    ".db", ".sqlite", ".sqlite3",
})


def is_binary(path: Path) -> bool:
    """Check if a file has a binary extension."""
    return path.suffix.lower() in _BINARY_EXTENSIONS


_SAFE_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "iso-8859-1")


def read_file_safe(path: Path) -> str | None:
    """Read a text file safely, returning None for binary/unreadable files."""
    if not path.is_file():
        return None
    if is_binary(path):
        return None
    for enc in _SAFE_ENCODINGS:
        try:
            text = path.read_text(encoding=enc, errors="strict")
            # Quick binary-content check: if non-text chars > 10%
            if _binary_score(text) > 0.1:
                return None
            return text
        except (UnicodeDecodeError, OSError):
            continue
    return None


def _binary_score(text: str) -> float:
    """Estimate the fraction of non-printable characters."""
    if not text:
        return 0.0
    control = sum(1 for c in text if ord(c) < 32 and c not in "\n\r\t")
    return control / len(text)


# ---------------------------------------------------------------------------
# Timestamp
# ---------------------------------------------------------------------------

def now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    source_path: Path,
    file_hash: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
):
    """Split text into overlapping chunks, yielding dicts for ChromaDB ingest.

    Yields dicts with keys: chunk_id, text, source_file, source_path, file_hash,
    chunk_index, indexed_at.
    """
    chunk_sz = chunk_size or _DEFAULT_CHUNK_SIZE
    ov = overlap or _DEFAULT_CHUNK_OVERLAP
    step = chunk_sz - ov
    if step < 1:
        step = chunk_sz
    now = now_iso()
    filename = source_path.name

    lines = text.splitlines(keepends=True)
    current = ""
    idx = 0
    for line in lines:
        # Handle lines longer than chunk_size by yielding partial chunks
        while len(current) + len(line) > chunk_sz and (current or len(line) > chunk_sz):
            room = chunk_sz - len(current)
            if room <= 0 and current:
                # Current buffer is full; yield it
                yield _make_chunk(current, source_path, file_hash, filename, idx, now)
                idx += 1
                if ov > 0 and len(current) > ov:
                    current = current[-ov:]
                else:
                    current = ""
                room = chunk_sz - len(current)
            # Take as much of the line as fits
            if room > 0 and line:
                current += line[:room]
                line = line[room:]
        current += line

    # Last chunk
    if current.strip():
        yield _make_chunk(current, source_path, file_hash, filename, idx, now)


def _make_chunk(text, source_path, file_hash, filename, idx, now):
    cid = chunk_id(source_path, idx, file_hash)
    return {
        "chunk_id": cid,
        "text": text,
        "source_file": filename,
        "source_path": str(source_path),
        "file_hash": file_hash,
        "chunk_index": idx,
        "indexed_at": now,
    }