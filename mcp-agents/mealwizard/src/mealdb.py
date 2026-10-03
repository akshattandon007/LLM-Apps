"""TheMealDB API client.

Free, zero-auth API. Base URL is configured via MEALDB_BASE_URL in .env
or defaults to https://www.themealdb.com/api/json/v1/1.

Endpoints used:
  - lookupmeal.php?i=<id>       — single recipe by ID
  - search.php?s=<query>        — search recipes by name
  - filter.php?i=<ingredients>  — filter by main ingredient (comma-separated)
  - filter.php?a=<area>         — filter by cuisine/area
  - filter.php?c=<category>     — filter by category
  - list.php?i=list             — list all ingredients
  - random.php                  — random meal
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from src.models import Recipe

BASE_URL = os.getenv(
    "MEALDB_BASE_URL",
    "https://www.themealdb.com/api/json/v1/1",
)
# Rate limit: ~10 req/s. 0.15s delay between calls keeps us well under.
REQUEST_DELAY = 0.15


class MealDBError(Exception):
    """Wraps API failures."""


class MealDBClient:
    """Thin wrapper around TheMealDB REST API."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=httpx.Timeout(timeout))

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def search_by_name(self, query: str) -> list[Recipe]:
        """Search recipes by name."""
        data = self._get("/search.php", params={"s": query})
        return self._parse_recipe_list(data)

    def lookup_by_id(self, meal_id: str) -> Optional[Recipe]:
        """Get a single recipe by its TheMealDB ID."""
        data = self._get("/lookupmeal.php", params={"i": meal_id})
        recipes = self._parse_recipe_list(data)
        return recipes[0] if recipes else None

    def filter_by_ingredient(self, ingredient: str) -> list[dict[str, Any]]:
        """Return lightweight meal summaries matching an ingredient."""
        data = self._get("/filter.php", params={"i": ingredient})
        return (data.get("meals") or []) if data else []

    def filter_by_area(self, area: str) -> list[dict[str, Any]]:
        """Filter by cuisine / area."""
        data = self._get("/filter.php", params={"a": area})
        return (data.get("meals") or []) if data else []

    def filter_by_category(self, category: str) -> list[dict[str, Any]]:
        """Filter by category (e.g. 'Seafood', 'Vegetarian')."""
        data = self._get("/filter.php", params={"c": category})
        return (data.get("meals") or []) if data else []

    def list_ingredients(self) -> list[dict[str, Any]]:
        """List all ingredients known to TheMealDB."""
        data = self._get("/list.php", params={"i": "list"})
        return (data.get("meals") or []) if data else []

    def random(self) -> Optional[Recipe]:
        """Fetch a random recipe."""
        data = self._get("/random.php")
        recipes = self._parse_recipe_list(data)
        return recipes[0] if recipes else None

    def lookup_batch(self, meal_ids: list[str]) -> list[Recipe]:
        """Fetch multiple recipes by ID (one API call each)."""
        results: list[Recipe] = []
        for mid in meal_ids:
            r = self.lookup_by_id(mid)
            if r:
                results.append(r)
        return results

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Make a GET request and return parsed JSON."""
        import time
        time.sleep(REQUEST_DELAY)
        url = f"{self.base_url}{path}"
        try:
            resp = self._client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            raise MealDBError(
                f"TheMealDB returned {exc.response.status_code} for {url}"
            ) from exc
        except httpx.RequestError as exc:
            raise MealDBError(f"Request to {url} failed: {exc}") from exc

    @staticmethod
    def _parse_recipe_list(data: dict[str, Any]) -> list[Recipe]:
        """Parse the 'meals' key from a TheMealDB response."""
        meals = data.get("meals") if data else None
        if not meals:
            return []
        return [Recipe.model_validate(m) for m in meals if m]