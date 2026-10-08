"""Tests for VibeCaster."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent to path so we can import vibecaster
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vibecaster import VibePackage, VibeClient


# ── Fixtures ────────────────────────────────────────────────────────────────

SAMPLE_RESPONSE = {
    "description": "A cozy, introspective evening — like sitting by a window while rain taps gently on the glass.",
    "palette": [
        {"hex": "#2C3E50", "name": "Midnight Blue"},
        {"hex": "#8B7355", "name": "Warm Bourbon"},
        {"hex": "#D4A574", "name": "Honey Glow"},
        {"hex": "#E8DFD0", "name": "Cream Silk"},
        {"hex": "#A0522D", "name": "Sienna Earth"},
    ],
    "poem": "Rain taps the window glass,\nA rhythm old and deep.\nThoughts wander like the smoke\nFrom a candle left to sleep.\nThe world outside is still,\nBut inside, something stirs.",
    "playlist": [
        {"title": "Holocene", "artist": "Bon Iver", "reason": "Haunting yet warm — matches the reflective quiet."},
        {"title": "River Flows in You", "artist": "Yiruma", "reason": "Gentle piano that mirrors the mood's soft edge."},
        {"title": "To Build a Home", "artist": "The Cinematic Orchestra", "reason": "Sweeping, emotive — perfect for introspection."},
    ],
    "vibe_shift": "Light a candle, make a cup of chamomile tea, and write down three things you're grateful for today.",
}


@pytest.fixture
def mock_completion():
    """Create a mock completion returning SAMPLE_RESPONSE."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(SAMPLE_RESPONSE)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    return mock_completion


@pytest.fixture
def client_with_key():
    """Return a VibeClient with a fake API key and mocked inner client."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test-key"}):
        c = VibeClient()
        c._client = MagicMock()
        return c


# ── Tests for VibePackage ───────────────────────────────────────────────────

def test_vibe_package_dataclass():
    """VibePackage should hold all expected fields with defaults."""
    vp = VibePackage(mood="peaceful")
    assert vp.mood == "peaceful"
    assert vp.palette_hexes == []
    assert vp.palette_names == []
    assert vp.poem == ""
    assert vp.playlist == []
    assert vp.vibe_shift == ""
    assert vp.description == ""


def test_vibe_package_full():
    """VibePackage with all fields populated."""
    vp = VibePackage(
        mood="energized",
        palette_hexes=["#FF5733", "#33FF57"],
        palette_names=["Vibrant Orange", "Fresh Green"],
        poem="Rise and shine!",
        playlist=[{"title": "Uptown Funk", "artist": "Bruno Mars", "reason": "Gets you moving"}],
        vibe_shift="Go for a brisk walk.",
        description="An energetic, vibrant mood.",
    )
    assert vp.mood == "energized"
    assert len(vp.palette_hexes) == 2
    assert len(vp.playlist) == 1


# ── Tests for VibeClient.generate ───────────────────────────────────────────

def test_client_generate(client_with_key, mock_completion):
    """Client.generate should parse AI response into VibePackage."""
    client_with_key._client.chat.completions.create.return_value = mock_completion

    result = client_with_key.generate("rainy evening introspection")

    assert isinstance(result, VibePackage)
    assert result.mood == "rainy evening introspection"
    assert len(result.palette_hexes) == 5
    assert result.palette_hexes[0] == "#2C3E50"
    assert result.palette_names[0] == "Midnight Blue"
    assert "Rain taps" in result.poem
    assert len(result.playlist) == 3
    assert result.playlist[0]["title"] == "Holocene"
    assert "candle" in result.vibe_shift


def test_client_generate_strips_fences(client_with_key):
    """Client should handle markdown-wrapped JSON."""
    fenced = f"```json\n{json.dumps(SAMPLE_RESPONSE)}\n```"
    mock_message = MagicMock()
    mock_message.content = fenced
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    client_with_key._client.chat.completions.create.return_value = mock_completion

    result = client_with_key.generate("moody")
    assert len(result.palette_hexes) == 5
    assert "Rain taps" in result.poem


def test_client_generate_no_fences(client_with_key):
    """Client should also handle plain JSON (no fences)."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(SAMPLE_RESPONSE)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    client_with_key._client.chat.completions.create.return_value = mock_completion

    result = client_with_key.generate("moody")
    assert result.palette_hexes[0] == "#2C3E50"


# ── Tests for API key resolution ────────────────────────────────────────────

def test_client_api_key_missing():
    """Client should raise RuntimeError when no API key is available."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("vibecaster.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            with pytest.raises(RuntimeError, match="No API key found"):
                VibeClient()


def test_client_from_openai_key():
    """Client should accept OPENAI_API_KEY as fallback."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-openai"}, clear=True):
        c = VibeClient()
        assert c.api_key == "sk-test-openai"


def test_env_file_fallback(tmp_path):
    """Should read API key from .env file when env var is missing."""
    env_file = tmp_path / ".env"
    env_file.write_text("OPENROUTER_API_KEY=sk-or-v1-test-key\nOTHER_VAR=blah")

    # Clear env except HOME set to tmp_path so Path(HOME)/.env resolves to our .env
    with patch.dict(os.environ, {"HOME": str(tmp_path)}, clear=True):
        c = VibeClient()
        assert c.api_key == "sk-or-v1-test-key"


# ── Tests for render ────────────────────────────────────────────────────────

def test_render_outputs_expected_sections(capsys):
    """Smoke test: render should print palette, poem, playlist, vibe_shift."""
    from vibecaster import render

    vp = VibePackage(
        mood="test mood",
        palette_hexes=["#FF0000", "#00FF00"],
        palette_names=["Red", "Green"],
        poem="Short test poem.",
        playlist=[{"title": "Test", "artist": "Tester", "reason": "Testing"}],
        vibe_shift="Do a test.",
        description="A test mood.",
    )
    try:
        render(vp)
    except Exception as e:
        pytest.fail(f"render() raised exception: {e}")

    captured = capsys.readouterr()
    output = captured.out
    assert "FF0000" in output, "Colour hex should appear"
    assert "Poem" in output or "poem" in output
    assert "Test" in output or "test" in output  # playlist or mood
    assert "shift" in output or "Vibe" in output or "vibe" in output


def test_render_empty_palette(capsys):
    """Render should not crash with empty palette."""
    from vibecaster import render

    vp = VibePackage(mood="quiet", description="A quiet mood.")
    try:
        render(vp)
    except Exception as e:
        pytest.fail(f"render() raised exception on minimal input: {e}")
    captured = capsys.readouterr()
    assert "quiet" in captured.out