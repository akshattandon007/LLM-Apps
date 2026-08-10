"""Smoke test: ingest sample records and verify answers."""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure we're in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

# Test configuration
DATA_DIR = PROJECT_ROOT / "data"
FAISS_INDEX = "/tmp/chart-faiss.index"


def test_ingest_and_query():
    """Full pipeline smoke test: ingest → query → verify."""
    from src.document_loader import load_document
    from src.chunker import chunk_document
    from src.embedder import embed_texts
    from src.vector_store import VectorStore
    from src.classifier import classify_intent
    from src.models import Intent

    print("=" * 60)
    print("CHART SMOKE TEST")
    print("=" * 60)

    # 1. Verify sample files exist
    pdf_files = sorted(DATA_DIR.glob("*.pdf"))
    txt_files = sorted(DATA_DIR.glob("*.txt"))

    assert len(pdf_files) >= 3, f"Expected at least 3 PDFs, found {len(pdf_files)}"
    assert len(txt_files) >= 3, f"Expected at least 3 TXT files, found {len(txt_files)}"
    print(f"\n[OK] Sample files found: {len(pdf_files)} PDFs, {len(txt_files)} TXTs")

    # 2. Clear old vector store
    vs = VectorStore(index_path=FAISS_INDEX)
    vs.clear()
    vs.save()
    print(f"[OK] Vector store cleared")

    # 3. Ingest all PDF files
    total_chunks = 0
    for pdf_path in pdf_files:
        doc = load_document(str(pdf_path))
        chunks = chunk_document(
            text=doc["text"],
            doc_id=pdf_path.stem,
            doc_type=doc["doc_type"],
            doc_name=doc["doc_name"],
            dates=doc["dates"],
            medications=doc["medications"],
            labs=doc["labs"],
            values=doc["values"],
        )
        texts = [c.text for c in chunks]
        embeddings = embed_texts(texts)
        vs.add(embeddings, chunks)
        total_chunks += len(chunks)
        print(f"  Ingested: {pdf_path.name} ({doc['doc_type'].value}) → {len(chunks)} chunks")

    vs.save()
    print(f"\n[OK] Total: {len(pdf_files)} docs → {total_chunks} chunks indexed")

    # 4. Test queries
    tests = [
        {
            "question": "What was my HbA1c in March 2023?",
            "expected_intent": Intent.LAB_VALUE,
            "check": ["5.7", "HbA1c"],
            "require_all": True,
        },
        {
            "question": "How did my LDL cholesterol change between March and September 2023?",
            "expected_intent": Intent.TEMPORAL_TREND,
            "check": ["130", "115", "LDL"],
            "require_all": True,
        },
        {
            "question": "When did I get my last tetanus shot?",
            "expected_intent": Intent.VACCINATION,
            "check": ["2022", "November", "tetanus"],
            "require_all": True,
        },
    ]

    for test in tests:
        q = test["question"]
        expected_intent = test["expected_intent"]
        checks = test["check"]

        print(f"\n--- Query: {q} ---")

        # Classify
        intent = classify_intent(q)
        assert intent == expected_intent, f"Expected intent {expected_intent.value}, got {intent.value}"
        print(f"[OK] Intent: {intent.value}")

        # Retrieve
        from src.embedder import embed_query
        query_emb = embed_query(q)
        results = vs.search(query_emb, top_k=5)
        assert len(results) > 0, f"No results retrieved for: {q}"
        print(f"[OK] Retrieved {len(results)} chunks (top score: {results[0][1]:.3f})")

        # Generate answer (local fallback, no API key)
        from src.rag_chain import _generate_local_answer
        answer = _generate_local_answer(q, [r[0] for r in results], intent)
        print(f"  Answer: {answer[:200]}...")

        # Verify answer contains expected values
        answer_lower = answer.lower()
        if test.get("require_all", False):
            missing = [c for c in checks if c.lower() not in answer_lower]
            assert len(missing) == 0, (
                f"Answer missing expected terms: {missing}\n"
                f"Expected all of: {checks}\n"
                f"Answer: {answer}"
            )
            print(f"[OK] Answer contains all: {', '.join(checks)}")
        else:
            found_checks = [c for c in checks if c.lower() in answer_lower]
            assert len(found_checks) > 0, (
                f"Answer did not contain any expected terms {checks}\n"
                f"Answer: {answer}"
            )
            print(f"[OK] Answer contains: {', '.join(found_checks)}")

    print("\n" + "=" * 60)
    print("ALL SMOKE TESTS PASSED")
    print("=" * 60)

    # Cleanup
    vs.clear()
    vs.save()


if __name__ == "__main__":
    test_ingest_and_query()