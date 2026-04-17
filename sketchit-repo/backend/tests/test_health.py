"""Tests for the /health endpoint."""


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_returns_json_shape(client):
    resp = client.get("/health")
    data = resp.get_json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "model" in data
    assert "api_key_configured" in data
    assert isinstance(data["api_key_configured"], bool)
