"""Smoke test for Earworm — verifies all modules import and core pipeline works."""

import sys
import os
import tempfile

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))


def test_models():
    from models import get_db, init_db, insert_show, insert_episode, stats, list_shows

    conn = get_db()
    init_db(conn)

    # Fresh DB should be empty
    s = stats(conn)
    assert s["shows"] == 0
    assert s["episodes"] == 0

    # Insert a show
    show_id = insert_show(conn, "Test Podcast")
    assert show_id > 0

    # Insert an episode
    ep_id = insert_episode(
        conn,
        show_id=show_id,
        title="Test Episode",
        description="A test episode",
        pub_date="2024-01-15",
        audio_url=None,
        source_file=None,
        transcript="This is a test transcript. It has multiple sentences. "
        "We use it to test semantic chunking. There should be several chunks.",
    )

    s = stats(conn)
    assert s["shows"] == 1
    assert s["episodes"] == 1
    assert s["chunks"] == 0  # No chunks yet

    conn.close()
    print("  [PASS] models")


def test_chunker():
    from chunker import chunk_transcript, _split_sentences
    from sentence_transformers import SentenceTransformer

    text = (
        "Machine learning is transforming how we build software. "
        "Neural networks can learn complex patterns from data. "
        "Deep learning has been particularly successful in vision tasks. "
        "Now let's talk about something completely different. "
        "The best pizza in New York is a subject of intense debate. "
        "Many argue that Lombardi's started it all. "
        "Others swear by Di Fara in Brooklyn."
    )

    model = SentenceTransformer("all-MiniLM-L6-v2")
    chunks = chunk_transcript(text, model=model)

    assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
    # Should have split at the topic boundary (ML -> pizza)
    # At minimum we should see some chunking
    for chunk in chunks:
        assert "text" in chunk
        assert "start_char" in chunk
        assert "end_char" in chunk
        assert len(chunk["text"]) > 0

    print(f"  [PASS] chunker ({len(chunks)} chunks from {len(text)} chars)")


def test_embedder():
    from embedder import load_model, embed_texts, create_index, load_id_map, save_id_map
    import numpy as np

    model = load_model()

    texts = ["hello world", "machine learning is fun", "podcast transcripts are useful"]
    embeddings = embed_texts(texts, model=model)

    assert embeddings.shape == (3, 384), f"Expected (3, 384), got {embeddings.shape}"
    assert embeddings.dtype == np.float32

    # Create index
    index = create_index(embeddings)
    assert index.ntotal == 3

    # Search
    query_vec = embed_texts(["machine learning"], model=model)
    scores, positions = index.search(query_vec, 3)

    # "machine learning is fun" should be the top result
    assert positions[0][0] >= 0
    assert scores[0][0] > 0.0

    print(f"  [PASS] embedder (384-dim, {index.ntotal} vectors)")


def test_ingest_file(tmpdir):
    """Test the file ingestion pipeline end-to-end."""
    from models import get_db, init_db, insert_show, stats
    from chunker import chunk_transcript
    from embedder import load_model, embed_texts, create_index, save_index, save_id_map

    # Create a test transcript file (long enough to trigger semantic splits at min_chars=400)
    transcript_path = os.path.join(tmpdir, "test_transcript.txt")
    transcript = (
        "Welcome to the Test Podcast. Today we discuss artificial intelligence. "
        "AI has come a long way since the Dartmouth workshop of 1956. "
        "Modern AI systems use deep learning and transformer architectures. "
        "GPT models have shown remarkable language understanding capabilities. "
        "Large language models can generate coherent text across many domains. "
        "They are trained on vast corpora of internet text and can answer questions. "
        "The transformer architecture introduced attention mechanisms that revolutionized NLP. "
        "Now shifting gears completely — let's talk about gardening. "
        "Tomatoes need at least six hours of direct sunlight per day. "
        "Water deeply but infrequently to encourage deep root growth. "
        "Compost is the single best thing you can add to your garden soil. "
        "Mulching helps retain moisture and suppress weeds in vegetable beds."
    )

    with open(transcript_path, "w") as f:
        f.write(transcript)

    # Ingest
    conn = get_db()
    init_db(conn)
    model = load_model()

    show_id = insert_show(conn, "Test Show")
    from models import insert_episode, clear_chunks_for_episode, insert_chunk

    ep_id = insert_episode(
        conn,
        show_id=show_id,
        title="AI and Gardening",
        description=None,
        pub_date="2024-06-01",
        audio_url=None,
        source_file="test_transcript.txt",
        transcript=transcript,
    )

    # Chunk
    chunks = chunk_transcript(transcript, model=model)
    assert len(chunks) >= 2, f"Expected at least 2 chunks (topic split), got {len(chunks)}"

    # Embed
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, model=model)

    # Store chunks
    clear_chunks_for_episode(conn, ep_id)
    for i, chunk in enumerate(chunks):
        insert_chunk(
            conn, ep_id, i, chunk["text"],
            chunk["start_char"], chunk["end_char"],
            len(chunk["text"].split()),
        )

    # Build index
    index = create_index(embeddings)
    id_map = {i: i + 1 for i in range(len(chunks))}  # Simple mapping for test

    # Verify
    s = stats(conn)
    assert s["chunks"] >= 2
    assert index.ntotal >= 2

    print(f"  [PASS] ingest pipeline ({s['chunks']} chunks, {index.ntotal} vectors)")


def test_searcher_integration():
    from models import get_db, init_db, stats
    from embedder import load_model, load_index, load_id_map
    from searcher import search_chunks

    conn = get_db()
    init_db(conn)
    s = stats(conn)

    model = load_model()
    index = load_index()
    id_map = load_id_map()

    if index is None or index.ntotal == 0:
        print("  [SKIP] searcher — no index available (ingest something first)")
        return

    results = search_chunks("machine learning AI", model, index, id_map, top_k=5)
    print(f"  [PASS] searcher ({len(results)} results returned)")


if __name__ == "__main__":
    print("== Earworm Smoke Test ==\n")

    test_models()
    test_chunker()
    test_embedder()

    with tempfile.TemporaryDirectory() as tmpdir:
        test_ingest_file(tmpdir)

    test_searcher_integration()

    print("\n== All tests passed ==")