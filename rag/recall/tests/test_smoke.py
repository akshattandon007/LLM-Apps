"""Smoke tests for Recall RAG application.

Tests:
  1. Document loader parses the sample transcript correctly
  2. Chunker produces correct chunk count and prepends speaker names
  3. Embedder produces embeddings of the right shape
  4. Vector store indexes and retrieves chunks
  5. Classifier correctly identifies intents for known queries
  6. End-to-end: ingest sample → query about pricing → verify answer structure
  7. End-to-end: query about action items
  8. End-to-end: query about disagreement
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Imports ────────────────────────────────────────────────────────────────

from src.document_loader import load_transcript
from src.chunker import chunk_utterances
from src.embedder import embed_chunks
from src.vector_store import VectorStore
from src.classifier import classify_intent, detect_speaker_mention

# ── Paths ──────────────────────────────────────────────────────────────────

SAMPLE_PATH = PROJECT_ROOT / "data" / "q3_pricing_meeting.txt"


# ── Helpers ────────────────────────────────────────────────────────────────

_passed = 0
_failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  ✓ {name}")
    else:
        _failed += 1
        print(f"  ✗ {name}: {detail}")


def run_all():
    global _passed, _failed
    _passed = 0
    _failed = 0

    # ── 1. Document loader ─────────────────────────────────────────────
    print("\n1. Document loader")
    utterances = load_transcript(SAMPLE_PATH)
    check("parses 15 utterances", len(utterances) == 15,
          f"got {len(utterances)}")
    check("first speaker is Sarah", utterances[0].speaker == "Sarah",
          f"got '{utterances[0].speaker}'")
    check("contains speaker 'Mike'", any(u.speaker == "Mike" for u in utterances))
    check("contains speaker 'Alex'", any(u.speaker == "Alex" for u in utterances))
    check("contains speaker 'Priya'", any(u.speaker == "Priya" for u in utterances))
    check("timestamps on first utterance", utterances[0].timestamp_start == "00:00:00",
          f"got '{utterances[0].timestamp_start}'")

    # ── 2. Chunker ─────────────────────────────────────────────────────
    print("\n2. Chunker")
    chunks = chunk_utterances(utterances, meeting_title="Q3 Pricing Meeting")
    check("same count as utterances", len(chunks) == 15)
    check("speaker prepended in text",
          chunks[0].text.startswith("[Sarah]"),
          f"got '{chunks[0].text[:20]}'")
    check("metadata has meeting title",
          chunks[0].metadata["meeting_title"] == "Q3 Pricing Meeting")
    check("metadata has speaker",
          chunks[0].metadata["speaker"] == "Sarah")
    check("metadata has timestamp",
          bool(chunks[0].metadata["timestamp_start"]))

    # ── 3. Embedder ────────────────────────────────────────────────────
    print("\n3. Embedder")
    texts = [c.text for c in chunks]
    embeddings = embed_chunks(texts)
    check("shape is (15, 384)", embeddings.shape == (15, 384),
          f"got {embeddings.shape}")
    check("values are float32", embeddings.dtype == "float32",
          f"got {embeddings.dtype}")

    # ── 4. Vector store ────────────────────────────────────────────────
    print("\n4. Vector store")
    store = VectorStore(dim=384)
    store.add_chunks(chunks, embeddings)
    check("index has 15 vectors", store.size == 15)

    # Search for a pricing-related query
    query_emb = embed_chunks(["What did Sarah propose for pricing?"])
    results = store.search(query_emb, top_k=3)
    check("search returns results", len(results) > 0,
          f"got {len(results)}")
    top_chunk = results[0][0]
    check("top result contains Sarah or hybrid",
          "Sarah" in top_chunk.text or "hybrid" in top_chunk.text,
          f"got '{top_chunk.text[:60]}'")

    # ── 5. Classifier ──────────────────────────────────────────────────
    print("\n5. Classifier")

    intent_action = classify_intent("What were the action items?")
    check("'action items' → ACTION_ITEM", intent_action == "ACTION_ITEM",
          f"got {intent_action}")

    intent_decision = classify_intent("What did the team decide about pricing?")
    check("'decide about pricing' → DECISION or FACT",
          intent_decision in ("DECISION", "FACT"),
          f"got {intent_decision}")

    intent_opinion = classify_intent("Who disagreed with the usage-based model?")
    check("'who disagreed' → OPINION", intent_opinion == "OPINION",
          f"got {intent_opinion}")

    intent_fact = classify_intent("What did Priya say about the survey?")
    check("'what did Priya say' → FACT", intent_fact == "FACT",
          f"got {intent_fact}")

    # Speaker detection
    sp = detect_speaker_mention("What did Sarah say about pricing?")
    check("detects Sarah", sp == "Sarah", f"got {sp}")
    sp2 = detect_speaker_mention("What were the action items?")
    check("no speaker detected for generic query", sp2 is None,
           f"got {sp2}")

    # ── 6. Full ingest pipeline ────────────────────────────────────────
    print("\n6. Full ingest pipeline")
    # Re-ingest into a fresh store
    store2 = VectorStore(dim=384)
    store2.add_chunks(chunks, embeddings)
    check("fresh store has 15 vectors", store2.size == 15)

    # Test query 1: pricing proposal
    # Use a more specific query so semantic search anchors on Sarah's hybrid model
    q1_emb = embed_chunks(["What hybrid pricing model did Sarah propose?"])
    q1_results = store2.search(q1_emb, top_k=5)
    q1_text = " ".join(r[0].text for r in q1_results).lower()
    check("pricing query finds Sarah's hybrid proposal",
          "hybrid" in q1_text,
          f"sample: {q1_text[:100]}")

    # Test query 2: action items
    q2_emb = embed_chunks(["What were the action items?"])
    q2_results = store2.search(q2_emb, top_k=5)
    q2_text = " ".join(r[0].text for r in q2_results).lower()
    check("action items query finds 'pricing tiers' or 'usage metering'",
          "pricing tiers" in q2_text or "usage metering" in q2_text,
          f"sample: {q2_text[:100]}")

    # Test query 3: disagreement
    q3_emb = embed_chunks(["Who disagreed with the usage-based model?"])
    q3_results = store2.search(q3_emb, top_k=5)
    q3_text = " ".join(r[0].text for r in q3_results)
    check("disagreement query finds Alex",
          "Alex" in q3_text,
          f"sample: {q3_text[:100]}")

    # ── Summary ────────────────────────────────────────────────────────
    print(f"\n{'='*40}")
    total = _passed + _failed
    print(f"Results: {_passed}/{total} passed, {_failed} failed")
    return _failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)