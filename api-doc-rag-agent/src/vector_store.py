"""
src/vector_store.py
───────────────────
Builds and wraps a FAISS vector store using HuggingFace sentence-transformers.
Keeps embeddings local — no extra API keys required for retrieval.
"""

from __future__ import annotations

import os
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from rich.console import Console

console = Console()

# Default embedding model: lightweight, 384-dim, runs on CPU in ~1-2s per batch
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def build_vector_store(
    documents: List[Document],
    embedding_model: str | None = None,
) -> FAISS:
    """
    Embed `documents` and build a FAISS in-memory vector store.

    Parameters
    ----------
    documents       : Chunked LangChain Documents from the doc loader.
    embedding_model : HuggingFace model name (overrides env / default).

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
        f"{len(documents)} chunks…[/bold cyan]"
    )

    vector_store = FAISS.from_documents(documents, embeddings)

    console.print(
        f"[bold green]✔  Vector store ready. "
        f"Index contains {vector_store.index.ntotal} vectors.[/bold green]\n"
    )
    return vector_store


def get_retriever(vector_store: FAISS, k: int = 5):
    """
    Wrap the FAISS store as a LangChain retriever.

    Parameters
    ----------
    vector_store : Built FAISS store.
    k            : Number of top chunks to retrieve per query.
    """
    return vector_store.as_retriever(
        search_type="mmr",           # Maximum Marginal Relevance — diversity + relevance
        search_kwargs={"k": k, "fetch_k": k * 3},
    )
