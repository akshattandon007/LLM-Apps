"""
src/vector_store.py
───────────────────
Builds and wraps a FAISS vector store using HuggingFace sentence-transformers.

Used by SpendLens to index transaction documents for semantic search — e.g.
"how much did I spend on coffee this month?" retrieves the relevant
transaction chunks before asking Claude.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from rich.console import Console

console = Console()

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Where to persist FAISS indices
DEFAULT_INDEX_DIR = Path(__file__).parent.parent / "data" / "faiss_index"


def build_vector_store(
    documents: list[Document],
    embedding_model: str | None = None,
    persist: bool = False,
    index_dir: str | Path | None = None,
) -> FAISS:
    """Embed transaction documents and build a FAISS vector store.

    Parameters
    ----------
    documents       : Chunked transaction Documents from document_loader.
    embedding_model : HuggingFace model name (overrides env / default).
    persist         : If True, save FAISS index to disk.
    index_dir       : Directory to persist the index (default: data/faiss_index/).

    Returns
    -------
    A FAISS retriever-ready vector store.
    """
    model_name = (
        embedding_model
        or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    )

    console.print(
        f"[bold cyan]⚙  Loading embedding model:[/bold cyan] {model_name}"
    )

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    console.print(
        f"[bold cyan]⚙  Building FAISS index from "
        f"{len(documents)} documents…[/bold cyan]"
    )

    vector_store = FAISS.from_documents(documents, embeddings)

    if persist:
        target_dir = Path(index_dir) if index_dir else DEFAULT_INDEX_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(target_dir))
        console.print(
            f"[bold green]✔  FAISS index persisted to {target_dir}[/bold green]"
        )

    console.print(
        f"[bold green]✔  Vector store ready. "
        f"Index contains {vector_store.index.ntotal} vectors.[/bold green]\n"
    )
    return vector_store


def load_vector_store(
    embedding_model: str | None = None,
    index_dir: str | Path | None = None,
) -> FAISS | None:
    """Load a previously persisted FAISS index from disk.

    Returns None if no persisted index exists.
    """
    target_dir = Path(index_dir) if index_dir else DEFAULT_INDEX_DIR

    if not target_dir.exists():
        console.print("[dim]No persisted index found.[/dim]")
        return None

    model_name = (
        embedding_model
        or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    )

    console.print(
        f"[bold cyan]⚙  Loading persisted FAISS index from {target_dir}[/bold cyan]"
    )

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    vector_store = FAISS.load_local(
        str(target_dir), embeddings, allow_dangerous_deserialization=True
    )
    console.print(
        f"[bold green]✔  Loaded index with {vector_store.index.ntotal} vectors.[/bold green]\n"
    )
    return vector_store


def get_retriever(
    vector_store: FAISS,
    k: int = 10,
    search_type: str = "mmr",
):
    """Wrap the FAISS store as a LangChain retriever.

    Parameters
    ----------
    vector_store : Built/loaded FAISS store.
    k            : Number of top chunks to retrieve per query.
    search_type  : 'mmr' (Maximum Marginal Relevance) or 'similarity'.
    """
    if search_type == "mmr":
        return vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": k * 3},
        )
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
