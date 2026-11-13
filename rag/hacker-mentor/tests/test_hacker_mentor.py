#!/usr/bin/env python3
"""Tests for Hacker Mentor RAG system."""

import sys
import os
import json
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from embedder import Embedder
from vector_store import VectorStore


def test_embedder_single():
    """Test embedding a single text string."""
    embedder = Embedder()
    vec = embedder.embed("What are the best practices for Python testing?")
    assert isinstance(vec, np.ndarray), f"Expected ndarray, got {type(vec)}"
    assert vec.shape == (384,), f"Expected shape (384,), got {vec.shape}"
    assert abs(np.linalg.norm(vec) - 1.0) < 0.01, "Expected normalized vector"


def test_embedder_batch():
    """Test embedding a batch of texts."""
    embedder = Embedder()
    texts = [
        "Python testing best practices",
        "Microservices architecture patterns",
        "Rust vs Go for backend services",
    ]
    vecs = embedder.embed_batch(texts)
    assert vecs.shape == (3, 384), f"Expected shape (3, 384), got {vecs.shape}"
    # Check all vectors are normalized
    for i in range(3):
        norm = np.linalg.norm(vecs[i])
        assert abs(norm - 1.0) < 0.01, f"Vector {i} not normalized: norm={norm}"


def test_vector_store_add_and_search():
    """Test adding embeddings and searching."""
    store = VectorStore(dim=384)
    embedder = Embedder()

    docs = [
        {"text": "Python is a great language for data science", "source": "comment",
         "story_title": "Python in 2024", "hn_url": "https://example.com/1",
         "points": 10, "author": "user1", "created_at": "2024-01-01"},
        {"text": "Rust offers memory safety without garbage collection", "source": "comment",
         "story_title": "Rust adoption", "hn_url": "https://example.com/2",
         "points": 15, "author": "user2", "created_at": "2024-01-02"},
        {"text": "Microservices add complexity but enable scaling", "source": "comment",
         "story_title": "Microservices at Netflix", "hn_url": "https://example.com/3",
         "points": 8, "author": "user3", "created_at": "2024-01-03"},
    ]

    texts = [d["text"] for d in docs]
    embeddings = embedder.embed_batch(texts)
    store.add(embeddings, docs)

    assert store.size == 3, f"Expected 3 docs, got {store.size}"

    # Search for Python-related query
    query_vec = embedder.embed("Tell me about Python programming")
    results = store.search(query_vec, k=2)

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    # First result should be about Python
    score, doc = results[0]
    assert "Python" in doc["text"], f"Expected Python doc, got: {doc['text'][:50]}"


def test_vector_store_save_load():
    """Test saving and loading the vector store."""
    # Create temp directory for test data
    import vector_store as vs
    original_data_dir = vs.DATA_DIR

    try:
        # Use temp directory
        tmpdir = tempfile.mkdtemp()
        vs.DATA_DIR = tmpdir

        embedder = Embedder()
        store = VectorStore(dim=384)

        docs = [
            {"text": "Docker containers simplify deployment", "source": "comment",
             "story_title": "Docker best practices", "hn_url": "https://example.com/1",
             "points": 12, "author": "dev1", "created_at": "2024-01-01"},
            {"text": "Kubernetes orchestrates container clusters", "source": "comment",
             "story_title": "K8s guide", "hn_url": "https://example.com/2",
             "points": 20, "author": "dev2", "created_at": "2024-01-02"},
        ]

        texts = [d["text"] for d in docs]
        embeddings = embedder.embed_batch(texts)
        store.add(embeddings, docs)
        store.save()

        # Load into new store
        store2 = VectorStore(dim=384)
        loaded = store2.load()
        assert loaded, "Expected load to return True"
        assert store2.size == 2, f"Expected 2 docs, got {store2.size}"

        # Search on reloaded store
        query_vec = embedder.embed("container orchestration")
        results = store2.search(query_vec, k=2)
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"

    finally:
        # Cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)
        vs.DATA_DIR = original_data_dir


def test_empty_store_search():
    """Test searching an empty store returns empty results."""
    store = VectorStore(dim=384)
    embedder = Embedder()
    query_vec = embedder.embed("test query")
    results = store.search(query_vec, k=5)
    assert results == [], f"Expected empty results, got {results}"


def test_add_empty_batch():
    """Test adding an empty batch doesn't crash."""
    store = VectorStore(dim=384)
    empty_embeddings = np.zeros((0, 384))
    store.add(empty_embeddings, [])
    assert store.size == 0


def test_metadata_integrity():
    """Test that metadata is correctly stored and retrievable."""
    store = VectorStore(dim=384)
    embedder = Embedder()

    doc = {"text": "Test document for metadata integrity", "source": "story",
           "story_title": "Test Story", "hn_url": "https://example.com/test",
           "points": 5, "author": "test_user", "created_at": "2024-06-15"}

    vec = embedder.embed(doc["text"])
    store.add(vec.reshape(1, -1), [doc])

    query_vec = embedder.embed("metadata integrity test")
    results = store.search(query_vec, k=1)

    assert len(results) == 1
    score, retrieved = results[0]
    assert retrieved["text"] == doc["text"]
    assert retrieved["author"] == "test_user"
    assert retrieved["points"] == 5
    assert retrieved["hn_url"] == "https://example.com/test"


if __name__ == "__main__":
    test_embedder_single()
    print("✅ test_embedder_single passed")
    test_embedder_batch()
    print("✅ test_embedder_batch passed")
    test_vector_store_add_and_search()
    print("✅ test_vector_store_add_and_search passed")
    test_vector_store_save_load()
    print("✅ test_vector_store_save_load passed")
    test_empty_store_search()
    print("✅ test_empty_store_search passed")
    test_add_empty_batch()
    print("✅ test_add_empty_batch passed")
    test_metadata_integrity()
    print("✅ test_metadata_integrity passed")
    print("\n🎉 All tests passed!")
