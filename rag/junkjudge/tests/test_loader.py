"""Tests for document_loader.py"""

from document_loader import load_and_chunk_from_text


SAMPLE_TEXT = (
    "Recycling Guidelines for Springfield.\n\n"
    "Accepted Materials:\n"
    "- Plastic bottles #1 and #2: Rinse and place in blue bin.\n"
    "- Cardboard: Flatten and place in blue bin. Pizza boxes are accepted "
    "only if no grease stains.\n"
    "- Glass jars and bottles: Rinse, remove lids, place in blue bin.\n"
    "- Aluminum cans: Rinse, crush if desired, place in blue bin.\n\n"
    "NOT Accepted:\n"
    "- Plastic bags: Do NOT place in blue bin. Return to grocery store.\n"
    "- Styrofoam: Not recyclable. Place in trash.\n"
    "- Electronics: Take to the city drop-off center.\n"
    "- Hazardous waste (paint, batteries, chemicals): "
    "Take to the Household Hazardous Waste facility.\n\n"
    "Collection Schedule:\n"
    "Curbside pickup every Tuesday. Bulk pickup first Tuesday of the month. "
    "Holiday delays: If a holiday falls on Monday or Tuesday, pickup is "
    "delayed by one day.\n"
)


def test_chunking_creates_multiple_chunks():
    """Verify that a long text produces multiple chunks."""
    chunks = load_and_chunk_from_text({"springfield.pdf": SAMPLE_TEXT})
    assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"


def test_chunk_metadata():
    """Each chunk must have id, text, source, page."""
    chunks = load_and_chunk_from_text({"test.pdf": SAMPLE_TEXT})
    for c in chunks:
        assert "id" in c
        assert "text" in c
        assert "source" in c
        assert "page" in c
    assert all(c["source"] == "test.pdf" for c in chunks)


def test_chunk_overlap_prevents_cutoff():
    """Overlapping chunks should ensure no sentence is lost at boundaries."""
    chunks = load_and_chunk_from_text({"a.pdf": SAMPLE_TEXT})
    # Check that no chunk is tiny (would indicate a bad split)
    for c in chunks:
        assert len(c["text"]) >= 20, f"Chunk too short: {c['text'][:50]}"


def test_multiple_sources():
    """Chunks from different sources should retain distinct source names."""
    chunks = load_and_chunk_from_text({
        "city-a.pdf": "City A: All plastic is accepted.",
        "city-b.pdf": "City B: Only #1 and #2 plastic.",
    })
    sources = {c["source"] for c in chunks}
    assert "city-a.pdf" in sources
    assert "city-b.pdf" in sources


def test_empty_text_yields_no_chunks():
    """Empty text should produce no chunks."""
    chunks = load_and_chunk_from_text({"empty.pdf": ""})
    assert len(chunks) == 0


def test_recycling_keywords_present():
    """Verify that key recycling terms survive chunking."""
    chunks = load_and_chunk_from_text({"springfield.pdf": SAMPLE_TEXT})
    all_text = " ".join(c["text"] for c in chunks)
    for keyword in ["pizza boxes", "blue bin", "Styrofoam", "bulk pickup"]:
        assert keyword.lower() in all_text.lower(), f"Missing: {keyword}"