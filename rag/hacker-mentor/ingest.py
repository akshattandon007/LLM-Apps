#!/usr/bin/env python3
"""
Ingest — fetch HN data, embed, and build the FAISS vector index.

Usage:
    python ingest.py --topic "microservices" --limit 50
"""

import argparse
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hn_fetcher import fetch_story_comments_batch
from embedder import Embedder
from vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingest HN data into vector index")
    parser.add_argument("--topic", default="programming", help="Search topic (default: programming)")
    parser.add_argument("--limit", type=int, default=30, help="Number of stories to fetch (max: 200)")
    parser.add_argument("--reindex", action="store_true", help="Force rebuild even if index exists")
    parser.add_argument("--comments", type=int, default=10, help="Max comments per story")
    args = parser.parse_args()

    store = VectorStore()

    # Check if index exists
    if not args.reindex and store.load():
        print(f"✅ Loaded existing index with {store.size} documents")
        print("   Use --reindex to rebuild from scratch")
        return

    print(f"🔍 Fetching HN stories about '{args.topic}'...")
    documents = fetch_story_comments_batch(
        topic=args.topic,
        story_limit=args.limit,
        comments_per_story=args.comments,
    )

    if not documents:
        print("❌ No documents found. Try a different topic.")
        return

    print(f"📄 Got {len(documents)} documents (stories + comments)")

    # Embed all documents
    print("🧠 Generating embeddings...")
    embedder = Embedder()
    texts = [d["text"] for d in documents]
    embeddings = embedder.embed_batch(texts)

    # Add to vector store
    store.add(embeddings, documents)
    store.save()

    print(f"✅ Indexed {store.size} documents into FAISS vector store")
    print(f"📁 Index saved to data/faiss_index.bin")
    print(f"📁 Metadata saved to data/metadata.json")

    # Print sample
    print(f"\n📋 Sample entries:")
    for doc in documents[:3]:
        print(f"  • [{doc['source']}] {doc['story_title'][:60]}")
        print(f"    {doc['hn_url']}")
    if len(documents) > 3:
        print(f"  ... and {len(documents) - 3} more")


if __name__ == "__main__":
    main()
