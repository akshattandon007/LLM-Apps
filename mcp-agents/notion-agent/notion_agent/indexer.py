"""Crawl the workspace and build a fresh vector index.

This is the one slow operation in the whole system (network-bound on the
crawl, CPU-bound on the embeddings). We run it as an explicit `index`
command rather than lazily so users know exactly when it's happening.
"""
from __future__ import annotations

import logging

from .notion_client_wrapper import NotionClientWrapper, NotionPage
from .vector_store import Chunk, VectorStore, chunk_text

logger = logging.getLogger(__name__)


def build_index(
    notion: NotionClientWrapper,
    store: VectorStore,
    chunk_size: int = 1800,
    overlap: int = 300,
) -> dict:
    """Crawl, chunk, embed, persist. Returns a summary dict."""
    all_chunks: list[Chunk] = []
    page_count = 0

    for page in notion.walk_workspace():
        page_count += 1
        chunks = _page_to_chunks(page, chunk_size=chunk_size, overlap=overlap)
        all_chunks.extend(chunks)
        logger.info("Indexed page %d: %s (%d chunks)", page_count, page.title, len(chunks))

    store.build(all_chunks)
    store.save()

    return {
        "pages": page_count,
        "chunks": len(all_chunks),
    }


def _page_to_chunks(page: NotionPage, chunk_size: int, overlap: int) -> list[Chunk]:
    """Turn one page into a list of indexable `Chunk`s."""
    if not page.text.strip():
        return []

    # Prefix each chunk with the page title so the embedding model has
    # topical context even when a chunk is just a bullet list.
    texts = chunk_text(page.text, chunk_size=chunk_size, overlap=overlap)
    return [
        Chunk(
            chunk_id=f"{page.page_id}:{i}",
            page_id=page.page_id,
            page_title=page.title,
            page_url=page.url,
            text=f"[Page: {page.title}]\n{text}",
            position=i,
        )
        for i, text in enumerate(texts)
    ]
