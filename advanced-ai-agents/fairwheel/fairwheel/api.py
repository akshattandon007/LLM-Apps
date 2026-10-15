"""HTTP layer for FairWheel.

Wraps httpx with a small client that can be swapped for a mock in tests via
set_client(). Every fetch is wrapped to raise HTTPError on anything non-200
so agents can fall back to simulated data cleanly.
"""

from __future__ import annotations

import httpx

_client: httpx.Client | None = None

DEFAULT_TIMEOUT = 15.0
USER_AGENT = "FairWheel/1.0 (car-purchase advisor; contact: n/a)"


class HTTPError(RuntimeError):
    """Raised when an upstream API returns non-200 or fails to connect."""


def set_client(client: httpx.Client | None) -> None:
    """Inject a mock client for hermetic tests."""
    global _client
    _client = client


def get_json(url: str, params: dict | None = None, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """GET a URL and return parsed JSON, raising HTTPError on failure."""
    client = _client or httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT})
    try:
        resp = client.get(url, params=params)
        if resp.status_code != 200:
            raise HTTPError(f"{url} returned HTTP {resp.status_code}")
        return resp.json()
    except httpx.HTTPError as exc:  # network errors, timeouts
        raise HTTPError(f"request to {url} failed: {exc}") from exc
    except ValueError as exc:  # bad JSON
        raise HTTPError(f"invalid JSON from {url}: {exc}") from exc
    finally:
        # Never close an injected mock client; only close one we created.
        if _client is None:
            client.close()


def get_text(url: str, params: dict | None = None, timeout: float = DEFAULT_TIMEOUT) -> str:
    """GET a URL and return raw text (for XML endpoints), raising HTTPError."""
    client = _client or httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT})
    try:
        resp = client.get(url, params=params)
        if resp.status_code != 200:
            raise HTTPError(f"{url} returned HTTP {resp.status_code}")
        return resp.text
    except httpx.HTTPError as exc:
        raise HTTPError(f"request to {url} failed: {exc}") from exc
    finally:
        if _client is None:
            client.close()