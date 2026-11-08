"""API module — fetches name data from Agify, Genderize, Nationalize, and Datamuse."""

import asyncio
from typing import Any

import httpx

AGIFY_URL = "https://api.agify.io/"
GENDERIZE_URL = "https://api.genderize.io/"
NATIONALIZE_URL = "https://api.nationalize.io/"
DATAMUSE_URL = "https://api.datamuse.com/words"

TIMEOUT = 10.0


async def _get(client: httpx.AsyncClient, url: str, params: dict[str, str]) -> Any:
    """Make an async GET request and return JSON, or None on failure."""
    try:
        resp = await client.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"error": str(exc)}


async def get_age(name: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    """Fetch age prediction from Agify.io."""
    async_client = client or httpx.AsyncClient()
    try:
        return await _get(async_client, AGIFY_URL, {"name": name}) or {}
    finally:
        if client is None:
            await async_client.aclose()


async def get_gender(name: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    """Fetch gender probability from Genderize.io."""
    async_client = client or httpx.AsyncClient()
    try:
        return await _get(async_client, GENDERIZE_URL, {"name": name}) or {}
    finally:
        if client is None:
            await async_client.aclose()


async def get_nationality(name: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    """Fetch country probabilities from Nationalize.io."""
    async_client = client or httpx.AsyncClient()
    try:
        return await _get(async_client, NATIONALIZE_URL, {"name": name}) or {}
    finally:
        if client is None:
            await async_client.aclose()


async def get_rhymes(name: str, client: httpx.AsyncClient | None = None) -> list[dict[str, Any]]:
    """Fetch rhyming words from Datamuse API."""
    async_client = client or httpx.AsyncClient()
    try:
        result = await _get(async_client, DATAMUSE_URL, {"rel_rhy": name})
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "error" in result:
            return [{"error": result["error"]}]
        return []
    finally:
        if client is None:
            await async_client.aclose()


async def fetch_all(name: str) -> dict[str, Any]:
    """Fetch all name data in parallel.

    Returns a dict with keys: age, gender, nationality, rhymes.
    """
    async with httpx.AsyncClient() as client:
        age_task = get_age(name, client)
        gender_task = get_gender(name, client)
        nationality_task = get_nationality(name, client)
        rhymes_task = get_rhymes(name, client)

        age_data, gender_data, nationality_data, rhymes_data = await asyncio.gather(
            age_task, gender_task, nationality_task, rhymes_task
        )

    return {
        "age": age_data,
        "gender": gender_data,
        "nationality": nationality_data,
        "rhymes": rhymes_data,
    }