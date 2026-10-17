"""Open Food Facts API client — text search and barcode lookup.

Uses only stdlib: urllib and json.  No API key required.
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional

BASE_URL = "https://world.openfoodfacts.org"
SEARCH_PATH = "/cgi/search.pl"
PRODUCT_PATH = "/api/v0/product"


def search_foods(query: str, page_size: int = 1) -> list[dict]:
    """Search products by name.  Returns list of product dicts."""
    params = urllib.parse.urlencode({
        "search_terms": query,
        "json": "1",
        "page_size": str(page_size),
    })
    url = f"{BASE_URL}{SEARCH_PATH}?{params}"
    data = _fetch_json(url)
    return data.get("products", [])


def lookup_barcode(barcode: str) -> Optional[dict]:
    """Look up a single product by barcode.  Returns product dict or None."""
    url = f"{BASE_URL}{PRODUCT_PATH}/{barcode}.json"
    data = _fetch_json(url)
    if data.get("status") == 1:
        return data.get("product")
    return None


def _fetch_json(url: str) -> dict:
    """Fetch and parse a JSON endpoint.  Empty dict on error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "pocketdiet/0.1.0 (cli tool)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError,
            OSError, ValueError):
        return {}