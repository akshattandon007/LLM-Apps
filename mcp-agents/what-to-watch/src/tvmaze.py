"""TVMaze API client — zero-auth, free, 60K+ shows."""

from __future__ import annotations

import httpx

BASE_URL = "https://api.tvmaze.com"
TIMEOUT = 15.0


class TVMazeError(Exception):
    """Wraps TVMaze API errors."""


class TVMazeClient:
    """Thin HTTP client for the TVMaze REST API."""

    def __init__(self, timeout: float = TIMEOUT) -> None:
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    # ---- Schedule ----

    def schedule(self, country: str = "US", date: str | None = None) -> list[dict]:
        """Full schedule by country for a given date (ISO: YYYY-MM-DD)."""
        params: dict[str, str] = {"country": country}
        if date:
            params["date"] = date
        return self._get("/schedule", params)

    def schedule_full(self, date: str | None = None) -> list[dict]:
        """Full schedule (all countries) for a date."""
        params: dict[str, str] = {}
        if date:
            params["date"] = date
        return self._get("/schedule/full", params)

    # ---- Search ----

    def search_show(self, query: str) -> list[dict]:
        """Search shows by name."""
        return self._get("/search/shows", {"q": query})

    def search_single_show(self, query: str) -> dict | None:
        """Single exact-match show search."""
        results = self._get("/singlesearch/shows", {"q": query})
        return results if isinstance(results, dict) else None

    # ---- Show lookup ----

    def show(self, show_id: int) -> dict:
        """Get a single show by TVMaze ID."""
        return self._get(f"/shows/{show_id}")

    def show_by_name(self, name: str) -> dict | None:
        """Get a single show by exact name match."""
        try:
            result = self._client.get(
                f"{BASE_URL}/singlesearch/shows",
                params={"q": name},
                timeout=TIMEOUT,
            )
            if result.status_code == 200:
                return result.json()
            return None
        except httpx.RequestError as exc:
            raise TVMazeError(f"Network error looking up show '{name}': {exc}") from exc

    # ---- Episodes ----

    def show_episodes(self, show_id: int) -> list[dict]:
        """Get all episodes for a show."""
        return self._get(f"/shows/{show_id}/episodes")

    # ---- Genres / Discovery ----

    def shows_page(self, page: int = 0) -> list[dict]:
        """Paginated show list (for genre discovery)."""
        return self._get("/shows", {"page": str(page)})

    # ---- Internal ----

    def _get(self, path: str, params: dict[str, str] | None = None) -> list[dict] | dict:
        url = f"{BASE_URL}{path}"
        try:
            resp = self._client.get(url, params=params, timeout=TIMEOUT)
        except httpx.RequestError as exc:
            raise TVMazeError(f"Network error: {exc}") from exc
        if resp.status_code == 429:
            raise TVMazeError("Rate-limited by TVMaze. Wait a moment and retry.")
        if resp.status_code != 200:
            raise TVMazeError(
                f"TVMaze returned {resp.status_code} for {path}: {resp.text[:200]}"
            )
        return resp.json()