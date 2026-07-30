"""Tests for /chat and /validate_key endpoints.

These tests mock out the Anthropic SDK so they run offline without a real
API key. After the per-request key change, we patch `server.Anthropic` —
the factory the /chat handler uses to construct a client per request.
"""

from unittest.mock import MagicMock, patch

# ---------- Helpers ----------


def _build_mock_response(text: str):
    """Build a mock Anthropic messages.create() response."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


def _mock_anthropic_returning(text: str):
    """
    Return (patch_context, mock_client). The patch replaces server.Anthropic
    with a factory that yields a mock whose messages.create() returns `text`.
    """
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _build_mock_response(text)
    factory = MagicMock(return_value=mock_client)
    return patch("server.Anthropic", factory), mock_client


# ---------- Basic validation ----------


def test_chat_requires_api_key(client):
    """With no env key and no body key, /chat returns 401 + error_code."""
    with patch("server.ENV_API_KEY", None):
        resp = client.post("/chat", json={"prompt": "x", "page_html": "<html/>"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["error_code"] == "missing_api_key"


def test_chat_requires_prompt(client):
    """Missing prompt should return 400 (when a key is present)."""
    resp = client.post(
        "/chat",
        json={"page_html": "<html></html>", "api_key": "sk-ant-test"},
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_chat_empty_prompt_rejected(client):
    """Empty prompt string should return 400."""
    resp = client.post(
        "/chat",
        json={"prompt": "   ", "page_html": "<html></html>", "api_key": "sk-ant-test"},
    )
    assert resp.status_code == 400


def test_chat_cors_preflight(client):
    """OPTIONS preflight should succeed."""
    resp = client.open("/chat", method="OPTIONS")
    assert resp.status_code == 204


# ---------- Success flow ----------


def test_chat_successful_response(client):
    """A clean JSON response from Claude should round-trip through /chat."""
    fake = '{"explanation": "Test", "operations": [{"type": "inject_css", "css": "body{}"}]}'
    ctx, _ = _mock_anthropic_returning(fake)
    with ctx:
        resp = client.post(
            "/chat",
            json={
                "prompt": "make it blue",
                "page_html": "<html></html>",
                "page_url": "https://test",
                "api_key": "sk-ant-test",
            },
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["explanation"] == "Test"
    assert len(data["operations"]) == 1
    assert data["operations"][0]["type"] == "inject_css"


def test_chat_strips_code_fences(client):
    """Model output wrapped in ```json fences should still parse."""
    fenced = '```json\n{"explanation": "ok", "operations": []}\n```'
    ctx, _ = _mock_anthropic_returning(fenced)
    with ctx:
        resp = client.post(
            "/chat",
            json={"prompt": "test", "page_html": "<html></html>", "api_key": "sk-ant-test"},
        )
    assert resp.status_code == 200
    assert resp.get_json()["explanation"] == "ok"


def test_chat_recovers_embedded_json(client):
    """If the model wraps JSON in prose, we should extract it."""
    messy = (
        'Sure! Here it is:\n\n{"explanation": "recovered", "operations": []}\n\nHope that helps!'
    )
    ctx, _ = _mock_anthropic_returning(messy)
    with ctx:
        resp = client.post(
            "/chat",
            json={"prompt": "test", "page_html": "<html></html>", "api_key": "sk-ant-test"},
        )
    assert resp.status_code == 200
    assert resp.get_json()["explanation"] == "recovered"


def test_chat_rejects_missing_operations_field(client):
    """A response without 'operations' should return 502."""
    bad = '{"explanation": "forgot operations"}'
    ctx, _ = _mock_anthropic_returning(bad)
    with ctx:
        resp = client.post(
            "/chat",
            json={"prompt": "test", "page_html": "<html></html>", "api_key": "sk-ant-test"},
        )
    assert resp.status_code == 502


def test_chat_handles_unparseable_output(client):
    """Totally garbled output should return 502."""
    garbage = "this is not JSON at all, just prose"
    ctx, _ = _mock_anthropic_returning(garbage)
    with ctx:
        resp = client.post(
            "/chat",
            json={"prompt": "test", "page_html": "<html></html>", "api_key": "sk-ant-test"},
        )
    assert resp.status_code == 502


def test_chat_truncates_large_html(client):
    """Page HTML over MAX_HTML should be truncated before sending to Claude."""
    huge = "<html>" + ("x" * 100_000) + "</html>"
    fake = '{"explanation": "ok", "operations": []}'
    ctx, mock_client = _mock_anthropic_returning(fake)
    with ctx:
        resp = client.post(
            "/chat",
            json={"prompt": "test", "page_html": huge, "api_key": "sk-ant-test"},
        )
        sent = mock_client.messages.create.call_args.kwargs["messages"]
        assert "truncated" in sent[-1]["content"]
    assert resp.status_code == 200


# ---------- Key-resolution tests ----------


def test_chat_prefers_request_key_over_env(client):
    """If both env key and body key are present, body key should win."""
    fake = '{"explanation": "ok", "operations": []}'
    ctx, _ = _mock_anthropic_returning(fake)
    with patch("server.ENV_API_KEY", "env-key"), ctx:
        resp = client.post(
            "/chat",
            json={"prompt": "test", "page_html": "<html/>", "api_key": "body-key"},
        )
        from server import Anthropic as patched_factory

        patched_factory.assert_called_with(api_key="body-key")
    assert resp.status_code == 200


def test_chat_falls_back_to_env_key(client):
    """If body has no key but env does, env key is used."""
    fake = '{"explanation": "ok", "operations": []}'
    ctx, _ = _mock_anthropic_returning(fake)
    with patch("server.ENV_API_KEY", "env-key"), ctx:
        resp = client.post(
            "/chat",
            json={"prompt": "test", "page_html": "<html/>"},
        )
        from server import Anthropic as patched_factory

        patched_factory.assert_called_with(api_key="env-key")
    assert resp.status_code == 200


def test_chat_auth_error_surfaces_invalid_key_code(client):
    """An authentication failure from Anthropic should return 401 + error_code."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("authentication_error: invalid api key")
    with patch("server.Anthropic", return_value=mock_client):
        resp = client.post(
            "/chat",
            json={"prompt": "test", "page_html": "<html/>", "api_key": "sk-ant-bad"},
        )
    assert resp.status_code == 401
    assert resp.get_json()["error_code"] == "invalid_api_key"


# ---------- /validate_key endpoint ----------


def test_validate_key_missing(client):
    """No key → 400, valid: false."""
    resp = client.post("/validate_key", json={})
    assert resp.status_code == 400
    assert resp.get_json()["valid"] is False


def test_validate_key_success(client):
    """A key the mocked SDK accepts → valid: true."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock()
    with patch("server.Anthropic", return_value=mock_client):
        resp = client.post("/validate_key", json={"api_key": "sk-ant-good"})
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is True


def test_validate_key_rejected(client):
    """An auth failure from the SDK → valid: false, 401."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("401 authentication_error")
    with patch("server.Anthropic", return_value=mock_client):
        resp = client.post("/validate_key", json={"api_key": "sk-ant-bad"})
    assert resp.status_code == 401
    assert resp.get_json()["valid"] is False
