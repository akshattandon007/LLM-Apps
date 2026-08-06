"""Earworm — semantic chunking using sentence boundary detection.

Splits transcripts at natural topic boundaries using sentence embeddings.
When two adjacent sentences' embeddings diverge beyond a threshold, a new
chunk boundary is inserted. Each chunk is 500-1000 chars, respecting
paragraph boundaries when possible.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import re


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving paragraph boundaries."""
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Split on sentence-ending punctuation followed by space or end
    sentences = re.split(r"(?<=[.!?])\s+", text)
    # Filter empty strings and very short fragments
    sentences = [s.strip() for s in sentences if len(s.strip()) > 2]
    return sentences


def _sentence_embeddings(
    sentences: list[str], model: SentenceTransformer
) -> np.ndarray:
    """Compute embeddings for a list of sentences."""
    if not sentences:
        return np.array([])
    return model.encode(sentences, show_progress_bar=False)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def chunk_transcript(
    text: str,
    model: SentenceTransformer | None = None,
    threshold: float = 0.35,
    min_chars: int = 400,
    max_chars: int = 1100,
) -> list[dict]:
    """Split transcript into semantically coherent chunks.

    Args:
        text: Full transcript text.
        model: SentenceTransformer model (loaded once, passed in).
        threshold: Cosine similarity below which a new chunk is started.
        min_chars: Minimum chunk size in characters.
        max_chars: Maximum chunk size in characters.

    Returns:
        List of dicts with keys: text, start_char, end_char.
    """
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    sentences = _split_sentences(text)
    if not sentences:
        return []

    # Compute embeddings for all sentences
    embeddings = _sentence_embeddings(sentences, model)

    # Build character offset map for each sentence
    offsets = []
    pos = 0
    for s in sentences:
        idx = text.find(s, pos)
        if idx < 0:
            idx = pos
        offsets.append((idx, idx + len(s)))
        pos = idx + len(s)

    chunks = []
    current_sentences = []
    current_start = offsets[0][0] if offsets else 0
    current_len = 0

    for i, (sentence, emb, (start, end)) in enumerate(
        zip(sentences, embeddings, offsets)
    ):
        candidate_len = current_len + len(sentence) + 1  # +1 for space

        # Decide whether to start a new chunk
        if current_sentences:
            sim = _cosine_similarity(embeddings[i - 1], emb)

            # Force break if adding this sentence would exceed max_chars
            force_break = (candidate_len > max_chars) and (
                current_len >= min_chars
            )

            # Semantic break: low similarity and we have enough content
            semantic_break = (sim < threshold) and (current_len >= min_chars)

            if force_break or semantic_break:
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    {
                        "text": chunk_text,
                        "start_char": current_start,
                        "end_char": current_start + len(chunk_text),
                    }
                )
                current_sentences = []
                current_start = start
                current_len = 0

        current_sentences.append(sentence)
        current_len += len(sentence) + 1

    # Final chunk
    if current_sentences:
        chunk_text = " ".join(current_sentences)
        chunks.append(
            {
                "text": chunk_text,
                "start_char": current_start,
                "end_char": current_start + len(chunk_text),
            }
        )

    # Merge very small trailing chunks into previous
    merged = []
    for chunk in chunks:
        clen = len(chunk["text"])
        if clen < min_chars and merged:
            prev = merged[-1]
            merged_text = prev["text"] + " " + chunk["text"]
            if len(merged_text) <= max_chars:
                merged[-1] = {
                    "text": merged_text,
                    "start_char": prev["start_char"],
                    "end_char": chunk["end_char"],
                }
                continue
        merged.append(chunk)

    return merged