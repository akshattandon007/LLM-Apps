"""Nager.Date API client — fetch public holidays and available countries.

Uses the free Nager.Date API (https://date.nager.at), no API key required.
"""

import json
import urllib.request
import urllib.error
from typing import Any

BASE_URL = "https://date.nager.at/api/v3"


def _urlopen(url: str) -> Any:
    """Thin wrapper for test injection via mock patching."""
    return urllib.request.urlopen(url)


def fetch_holidays(country_code: str, year: int) -> list[dict]:
    """Fetch public holidays for a country and year.

    Returns a list of dicts with keys: date, localName, name, countryCode,
    fixed, global, counties, launchYear, types.
    """
    url = f"{BASE_URL}/publicholidays/{year}/{country_code.upper()}"
    with _urlopen(url) as resp:
        return json.loads(resp.read().decode())


def fetch_countries() -> list[dict]:
    """Fetch all supported countries.

    Returns list of dicts: {countryCode, name}
    """
    url = f"{BASE_URL}/AvailableCountries"
    with _urlopen(url) as resp:
        return json.loads(resp.read().decode())