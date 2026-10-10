"""Shared test helpers: fixture loading and a network-free httpx client.

Every test runs against httpx.MockTransport — no test ever hits the
network.  Responses are routed by URL path:
  /v1/search       → geocode fixture
  /v1/air-quality  → air-quality fixture
"""

from __future__ import annotations

import json
import pathlib

import httpx

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture from tests/fixtures/."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_http_client(
    air_quality: dict | None = None,
    geocode: dict | None = None,
    status: int = 200,
) -> httpx.Client:
    """Build httpx.Client with MockTransport serving canned responses."""
    air_quality = (
        air_quality
        if air_quality is not None
        else load_fixture("air_quality_sample.json")
    )
    geocode = (
        geocode if geocode is not None else load_fixture("geo_sample.json")
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if "/v1/search" in request.url.path:
            return httpx.Response(status, json=geocode)
        if "/v1/air-quality" in request.url.path:
            return httpx.Response(status, json=air_quality)
        return httpx.Response(404, json={"error": "fixture: no route"})

    return httpx.Client(transport=httpx.MockTransport(handler))


def make_client(
    air_quality: dict | None = None,
    geocode: dict | None = None,
    status: int = 200,
):
    """OpenMeteoClient wired to canned fixtures (no network)."""
    from breatheasy.api import OpenMeteoClient

    return OpenMeteoClient(make_http_client(air_quality, geocode, status))