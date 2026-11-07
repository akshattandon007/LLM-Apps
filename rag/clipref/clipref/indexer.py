"""ClipRef — indexer: file scanning, chunking, embedding, and ChromaDB storage."""

from __future__ import annotations

import os
import time
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from clipref import utils
from clipref.models import (
    ChunkMetadata,
    IndexStats,
)


def scan_files(paths: list[str], glob_pattern: str | None = None) -> list[Path]:
    """Recursively scan paths for text files matching the glob.

    Args:
        paths: One or more file/directory paths.
        glob_pattern: Glob pattern to filter files (default: ``*.*`` — all text extensions).

    Returns:
        Sorted list of unique file paths.
    """
    if glob_pattern is None:
        # Default: match common text file extensions
        pattern = "[!.]*.*"  # exclude hidden files
    else:
        pattern = glob_pattern

    seen: set[Path] = set()

    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            continue
        if p.is_file():
            if _matches_glob(p, pattern):
                seen.add(p)
        elif p.is_dir():
            # Walk recursively
            for found in _walk_text_files(p, pattern):
                seen.add(found)

    result = sorted(seen, key=lambda x: x.resolve())
    return result


def _walk_text_files(directory: Path, pattern: str) -> list[Path]:
    """Walk a directory, yielding text files matching the glob."""
    files: list[Path] = []
    try:
        for entry in directory.rglob("*"):
            if entry.is_file() and _matches_glob(entry, pattern):
                if not entry.name.startswith("."):
                    files.append(entry)
    except PermissionError:
        pass
    return files


def _matches_glob(path: Path, pattern: str) -> bool:
    """Check if a file path matches a glob pattern."""
    from fnmatch import fnmatch
    return fnmatch(path.name, pattern)


def chunk_files(
    files: list[Path],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[dict]:
    """Read and chunk text files into document dicts.

    Returns:
        List of chunk dicts ready for embedding + storage.
    """
    chunks: list[dict] = []
    skipped = 0

    for path in files:
        if utils.is_binary(path):
            skipped += 1
            continue
        text = utils.read_file_safe(path)
        if text is None:
            skipped += 1
            continue
        file_hash = utils.hash_file(path)
        for chunk in utils.chunk_text(text, path, file_hash, chunk_size, overlap):
            chunks.append(chunk)

    if skipped:
        print(f"  (skipped {skipped} binary/unreadable files)")
    return chunks


# ---------------------------------------------------------------------------
# ChromaDB client helpers
# ---------------------------------------------------------------------------


def _get_client(db_path: Path) -> chromadb.ClientAPI:
    """Get or create a ChromaDB client at the given path."""
    db_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(db_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_collection(client: chromadb.ClientAPI, name: str):
    """Get or create a collection by name."""
    try:
        return client.get_collection(name)
    except (ValueError, chromadb.errors.NotFoundError):
        return client.create_collection(name)


# ---------------------------------------------------------------------------
# Embed + store
# ---------------------------------------------------------------------------


def embed_and_store(
    chunks: list[dict],
    model,
    db_path: Path,
    batch_size: int = 64,
):
    """Embed chunk texts and store in ChromaDB.

    Args:
        chunks: List of chunk dicts from ``chunk_files()``.
        model: SentenceTransformer model instance.
        db_path: Directory path for ChromaDB persistence.
        batch_size: How many chunks to process per batch.

    Returns:
        Number of chunks stored.
    """
    if not chunks:
        return 0

    client = _get_client(db_path)
    collection = _get_collection(client, utils.collection_name())

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [
        {
            "source_file": c["source_file"],
            "source_path": c["source_path"],
            "file_hash": c["file_hash"],
            "chunk_index": c["chunk_index"],
            "indexed_at": c["indexed_at"],
        }
        for c in chunks
    ]

    stored = 0
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]
        batch_embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            metadatas=batch_meta,
            documents=batch_texts,
        )
        stored += len(batch_texts)

    return stored


# ---------------------------------------------------------------------------
# Stats / drop
# ---------------------------------------------------------------------------


def get_stats(db_path: Path) -> IndexStats | None:
    """Get index statistics, or None if the collection doesn't exist."""
    client = _get_client(db_path)
    try:
        collection = client.get_collection(utils.collection_name())
    except (ValueError, chromadb.errors.NotFoundError):
        return None

    chunk_count = collection.count()
    # Count unique source files from metadata (sample up to 10K chunks)
    all_meta = collection.get(limit=chunk_count if chunk_count < 10000 else 10000)
    if not all_meta or not all_meta.get("metadatas"):
        return IndexStats(chunk_count=chunk_count, source_files=0, database_size_bytes=0)

    unique_files = set()
    for m in all_meta["metadatas"]:
        if m and "source_path" in m:
            unique_files.add(m["source_path"])

    # Estimate source files if we sampled
    source_files = len(unique_files) if chunk_count < 10000 else f"{len(unique_files)}+"

    # Database size
    db_size = 0
    try:
        for entry in db_path.rglob("*"):
            if entry.is_file():
                db_size += entry.stat().st_size
    except OSError:
        pass

    return IndexStats(
        chunk_count=chunk_count,
        source_files=source_files if isinstance(source_files, int) else 0,
        database_size_bytes=db_size,
    )


def drop_index(db_path: Path) -> bool:
    """Delete the ChromaDB collection."""
    client = _get_client(db_path)
    try:
        # Check if collection exists first
        client.get_collection(utils.collection_name())
        client.delete_collection(utils.collection_name())
        return True
    except (ValueError, chromadb.errors.NotFoundError):
        # Collection doesn't exist
        return False