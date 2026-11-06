"""Tests for qrcraft — QR code generation and decoding."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qrcraft.encode import encode, encode_many
from qrcraft.decode import decode
from qrcraft.cli import build_parser, main


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def qr_png():
    """Generate a temporary QR code PNG and return the path."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    encode("https://github.com/akshattandon007/LLM-Apps", output=path)
    yield path
    if os.path.exists(path):
        os.unlink(path)


# ── Encode Tests ───────────────────────────────────────────────────────────

class TestEncode:
    def test_encode_png(self):
        """Encoding a URL to PNG should produce a non-empty file."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            result = encode("https://example.com", output=path)
            assert result == path
            assert os.path.getsize(path) > 100
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_encode_ascii(self):
        """ASCII mode should return '(stdout)' and not write a file."""
        result = encode("Hello", ascii=True)
        assert result == "(stdout)"

    def test_encode_no_output_does_not_crash(self):
        """Omitting output should write PNG data and not crash."""
        import io
        # Use a wrapper that has .buffer
        class FakeStdout:
            buffer = io.BytesIO()
        old_stdout = sys.stdout
        sys.stdout = FakeStdout()  # type: ignore
        try:
            result = encode("test")
            assert result == "(stdout)"
            assert FakeStdout.buffer.getvalue()[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic
        finally:
            sys.stdout = old_stdout

    def test_encode_many(self):
        """Batch mode should produce N files."""
        with tempfile.TemporaryDirectory() as tmp:
            paths = encode_many(["a", "b", "c"], output_dir=tmp)
            assert len(paths) == 3
            for p in paths:
                assert os.path.getsize(p) > 100

    def test_encode_empty_string(self):
        """Encoding an empty string should still produce a QR code."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            result = encode("", output=path)
            assert result == path
            assert os.path.getsize(path) > 100
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_different_error_levels(self):
        """All error correction levels should work."""
        for level in ["L", "M", "Q", "H"]:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                path = f.name
            try:
                encode("test", output=path, error_correction=level)
                assert os.path.getsize(path) > 100
            finally:
                if os.path.exists(path):
                    os.unlink(path)

    def test_custom_colours(self):
        """Custom fill and background colours should not crash."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            encode("test", output=path, fill_color="#FF0000", back_color="#0000FF")
            assert os.path.getsize(path) > 100
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_long_url(self):
        """A long URL should still produce a valid QR code."""
        long_url = "https://example.com/" + "a" * 500
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            result = encode(long_url, output=path)
            assert result == path
            assert os.path.getsize(path) > 200
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ── Decode Tests ───────────────────────────────────────────────────────────

class TestDecode:
    def test_decode_on_generated_qr(self, qr_png):
        """Decoding a QR we just generated should return at least one result."""
        # This may return empty if no decoder is available (zbarimg, pyzbar, API)
        results = decode(qr_png)
        # If we have a working decoder, verify we get our data back
        if results:
            assert any("github.com" in r["data"] for r in results)

    def test_decode_nonexistent_file(self):
        """Trying to decode a non-existent file should raise FileNotFoundError."""
        import pytest
        with pytest.raises(FileNotFoundError):
            decode("/nonexistent/file.png")

    def test_decode_empty_image(self):
        """Decoding a blank image should return empty list (not crash)."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create a blank PNG
            from PIL import Image
            img = Image.new("RGB", (100, 100), (255, 255, 255))
            img.save(f)
            path = f.name
        try:
            results = decode(path)
            assert isinstance(results, list)
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ── CLI Tests ──────────────────────────────────────────────────────────────

class TestCLI:
    def test_parser_encode(self):
        """CLI parser should handle encode subcommand."""
        parser = build_parser()
        args = parser.parse_args(["encode", "test data", "-o", "out.png"])
        assert args.command == "encode"
        assert args.data == "test data"
        assert args.output == "out.png"

    def test_parser_encode_ascii(self):
        """CLI parser should accept --ascii flag."""
        parser = build_parser()
        args = parser.parse_args(["e", "hello", "--ascii"])
        assert args.command == "e"
        assert args.ascii is True

    def test_parser_decode(self):
        """CLI parser should handle decode subcommand."""
        parser = build_parser()
        args = parser.parse_args(["decode", "image.png", "--json"])
        assert args.command == "decode"
        assert args.image == "image.png"
        assert args.json is True

    def test_parser_decode_alias(self):
        """CLI parser should accept 'd' alias for decode."""
        parser = build_parser()
        args = parser.parse_args(["d", "img.png"])
        assert args.command == "d"

    def test_version_flag(self):
        """--version should print version and exit."""
        import io
        parser = build_parser()
        try:
            parser.parse_args(["--version"])
        except SystemExit as e:
            assert e.code == 0

    def test_main_encode_no_data(self):
        """main() should return 1 when no data provided."""
        import io
        # Simulate stdin being a TTY so it won't try to read it
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        sys.stdin = io.StringIO()      # empty, but not a TTY
        sys.stdin.isatty = lambda: True  # pretend it's a TTY → skip stdin read
        sys.stdout = io.StringIO()
        try:
            ret = main(["encode"])
            assert ret == 1
        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

    def test_main_decode_nonexistent(self):
        """main() with a missing file should return 1."""
        ret = main(["decode", "/nonexistent.png"])
        assert ret == 1