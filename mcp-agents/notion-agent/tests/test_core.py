"""Unit tests for the pure-logic parts of notion_agent.

These deliberately avoid touching the network or hitting either API.
"""
from __future__ import annotations

from notion_agent.notion_client_wrapper import _block_to_text, _normalise_id, _split_for_notion
from notion_agent.vector_store import chunk_text


class TestNormaliseId:
    def test_plain_hex_id(self):
        raw = "a" * 32
        assert _normalise_id(raw) == f"{'a'*8}-{'a'*4}-{'a'*4}-{'a'*4}-{'a'*12}"

    def test_already_dashed(self):
        dashed = "12345678-1234-1234-1234-123456781234"
        assert _normalise_id(dashed) == dashed

    def test_url_form(self):
        url = "https://www.notion.so/myorg/My-Page-abcdef0123456789abcdef0123456789"
        assert _normalise_id(url) == "abcdef01-2345-6789-abcd-ef0123456789"

    def test_uppercase_is_lowercased(self):
        raw = "A" * 32
        assert _normalise_id(raw) == f"{'a'*8}-{'a'*4}-{'a'*4}-{'a'*4}-{'a'*12}"


class TestBlockToText:
    def _block(self, btype: str, text: str, **extra):
        payload = {
            "rich_text": [{"plain_text": text}],
            **extra,
        }
        return {"type": btype, btype: payload}

    def test_heading_1(self):
        assert _block_to_text(self._block("heading_1", "Intro")) == "# Intro"

    def test_bulleted(self):
        assert _block_to_text(self._block("bulleted_list_item", "one")) == "- one"

    def test_todo_unchecked(self):
        out = _block_to_text(self._block("to_do", "ship", checked=False))
        assert out == "- [ ] ship"

    def test_todo_checked(self):
        out = _block_to_text(self._block("to_do", "ship", checked=True))
        assert out == "- [x] ship"

    def test_code_block_includes_language(self):
        out = _block_to_text(self._block("code", "print('hi')", language="python"))
        assert out == "```python\nprint('hi')\n```"

    def test_unsupported_block_type_returns_empty(self):
        assert _block_to_text({"type": "divider", "divider": {}}) == ""

    def test_empty_rich_text_returns_empty(self):
        b = {"type": "paragraph", "paragraph": {"rich_text": []}}
        assert _block_to_text(b) == ""


class TestSplitForNotion:
    def test_short_text_not_split(self):
        assert _split_for_notion("hi", limit=100) == ["hi"]

    def test_long_text_is_split(self):
        text = ("word " * 1000).strip()
        chunks = _split_for_notion(text, limit=500)
        assert len(chunks) > 1
        assert all(len(c) <= 500 for c in chunks)

    def test_paragraphs_preserved(self):
        text = "para one\npara two\npara three"
        chunks = _split_for_notion(text, limit=100)
        assert len(chunks) == 1


class TestChunkText:
    def test_short_text_single_chunk(self):
        assert chunk_text("hello world", chunk_size=1000, overlap=50) == ["hello world"]

    def test_empty_text_no_chunks(self):
        assert chunk_text("", chunk_size=1000, overlap=50) == []
        assert chunk_text("   \n  ", chunk_size=1000, overlap=50) == []

    def test_splits_long_text(self):
        paragraphs = [f"paragraph number {i} with some content" for i in range(100)]
        text = "\n".join(paragraphs)
        chunks = chunk_text(text, chunk_size=300, overlap=50)
        assert len(chunks) > 1
        # Overlap means chunks after the first have a tail from the previous.
        # Each still shouldn't be wildly oversized.
        assert all(len(c) <= 400 for c in chunks)

    def test_very_long_paragraph_is_hard_sliced(self):
        long_para = "x" * 5000
        chunks = chunk_text(long_para, chunk_size=1000, overlap=100)
        assert len(chunks) > 1
        # First chunk is 1000 chars; subsequent chunks are prefixed with overlap.
        assert len(chunks[0]) == 1000
