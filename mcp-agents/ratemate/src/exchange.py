"""Frankfurter exchange-rate API client — zero-auth, free."""

from __future__ import annotations

import httpx

BASE_URL = "https://api.frankfurter.dev/v1"

CURRENCY_NAMES: dict[str, str] = {
    "AUD": "Australian Dollar",
    "BGN": "Bulgarian Lev",
    "BRL": "Brazilian Real",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan Renminbi",
    "CZK": "Czech Koruna",
    "DKK": "Danish Krone",
    "EUR": "Euro",
    "GBP": "British Pound",
    "HKD": "Hong Kong Dollar",
    "HRK": "Croatian Kuna",
    "HUF": "Hungarian Forint",
    "IDR": "Indonesian Rupiah",
    "ILS": "Israeli New Shekel",
    "INR": "Indian Rupee",
    "ISK": "Icelandic Krona",
    "JPY": "Japanese Yen",
    "KRW": "South Korean Won",
    "MXN": "Mexican Peso",
    "MYR": "Malaysian Ringgit",
    "NOK": "Norwegian Krone",
    "NZD": "New Zealand Dollar",
    "PHP": "Philippine Peso",
    "PLN": "Polish Zloty",
    "RON": "Romanian New Leu",
    "SEK": "Swedish Krona",
    "SGD": "Singapore Dollar",
    "THB": "Thai Baht",
    "TRY": "Turkish Lira",
    "USD": "United States Dollar",
    "ZAR": "South African Rand",
}


async def latest_rates(from_currency: str = "USD") -> dict | None:
    """Get latest exchange rates relative to *from_currency*."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{BASE_URL}/latest", params={"from": from_currency})
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "base": data["base"],
            "date": data["date"],
            "rates": data["rates"],
        }


async def convert(
    amount: float,
    from_currency: str,
    to_currency: str,
    date: str | None = None,
) -> dict | None:
    """Convert *amount* from *from_currency* to *to_currency*.

    Optionally use a historical *date* (YYYY-MM-DD).  Uses the latest rate
    when *date* is None.
    """
    endpoint = f"{BASE_URL}/{date}" if date else f"{BASE_URL}/latest"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            endpoint,
            params={"from": from_currency, "to": to_currency},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        rate = data["rates"].get(to_currency)
        if rate is None:
            return None
        return {
            "amount": amount,
            "from": from_currency,
            "to": to_currency,
            "rate": rate,
            "result": round(amount * rate, 2),
            "date": data.get("date", date or "latest"),
        }


async def list_currencies() -> dict[str, str] | None:
    """Get all supported currency codes and their names."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{BASE_URL}/currencies")
        if resp.status_code != 200:
            return None
        return resp.json()  # {"EUR": "Euro", ...}


async def historical_range(
    from_currency: str,
    to_currency: str,
    from_date: str,
    to_date: str,
) -> dict | None:
    """Get exchange-rate history between *from_date* and *to_date*."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{BASE_URL}/{from_date}..{to_date}",
            params={"from": from_currency, "to": to_currency},
        )
        if resp.status_code != 200:
            return None
        return resp.json()