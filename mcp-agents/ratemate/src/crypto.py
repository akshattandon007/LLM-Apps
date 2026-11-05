"""CoinGecko API client — free tier, no API key needed."""

from __future__ import annotations

import httpx

BASE_URL = "https://api.coingecko.com/api/v3"

# Pre-curated useful coin list
POPULAR_COINS: dict[str, str] = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "tether": "Tether",
    "ripple": "XRP",
    "cardano": "Cardano",
    "solana": "Solana",
    "polkadot": "Polkadot",
    "dogecoin": "Dogecoin",
    "avalanche-2": "Avalanche",
    "chainlink": "Chainlink",
}


async def get_price(coin_id: str, vs_currency: str = "usd") -> dict | None:
    """Get the current price for a single coin."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{BASE_URL}/simple/price",
            params={"ids": coin_id, "vs_currencies": vs_currency},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if coin_id not in data:
            return None
        price = data[coin_id].get(vs_currency)
        return {"coin": coin_id, "currency": vs_currency.upper(), "price": price}


async def get_top_coins(limit: int = 10, vs_currency: str = "usd") -> list[dict] | None:
    """Get top N coins by market cap."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{BASE_URL}/coins/markets",
            params={
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": min(limit, 250),
                "page": 1,
                "sparkline": "false",
            },
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return [
            {
                "rank": i + 1,
                "coin": item["id"],
                "name": item["symbol"].upper(),
                "price": item["current_price"],
                "market_cap": item["market_cap"],
                "change_24h": item["price_change_percentage_24h"],
            }
            for i, item in enumerate(data[:limit])
        ]


async def coin_info(coin_id: str) -> dict | None:
    """Get detailed info about a specific coin."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{BASE_URL}/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
            },
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "name": data.get("name"),
            "symbol": data.get("symbol", "").upper(),
            "current_price_usd": data.get("market_data", {}).get("current_price", {}).get("usd"),
            "market_cap_rank": data.get("market_data", {}).get("market_cap_rank"),
            "total_volume_usd": data.get("market_data", {}).get("total_volume", {}).get("usd"),
            "high_24h_usd": data.get("market_data", {}).get("high_24h", {}).get("usd"),
            "low_24h_usd": data.get("market_data", {}).get("low_24h", {}).get("usd"),
            "price_change_24h_pct": data.get("market_data", {}).get("price_change_percentage_24h"),
            "all_time_high_usd": data.get("market_data", {}).get("ath", {}).get("usd"),
            "description": (data.get("description", {}) or {}).get("en", "")[:500] if data.get("description") else "",
        }