"""Tests for crypto module — CoinGecko API integration."""

from __future__ import annotations

import pytest

from src.crypto import get_price, get_top_coins, coin_info, POPULAR_COINS


@pytest.mark.asyncio
async def test_get_price_bitcoin() -> None:
    """Bitcoin price should be a positive number."""
    result = await get_price("bitcoin", "usd")
    assert result is not None
    assert result["coin"] == "bitcoin"
    assert result["currency"] == "USD"
    assert result["price"] > 0
    assert isinstance(result["price"], (int, float))


@pytest.mark.asyncio
async def test_get_price_ethereum() -> None:
    """Ethereum price should be positive."""
    result = await get_price("ethereum", "usd")
    assert result is not None
    assert result["price"] > 0


@pytest.mark.asyncio
async def test_get_price_unknown_coin() -> None:
    """Unknown coin ID should return None."""
    result = await get_price("nonexistent_coin_fake_12345", "usd")
    assert result is None


@pytest.mark.asyncio
async def test_get_top_coins_default() -> None:
    """Top 10 coins should return at least 5 entries."""
    result = await get_top_coins(10)
    assert result is not None
    assert len(result) >= 5
    assert result[0]["rank"] == 1


@pytest.mark.asyncio
async def test_coin_info_bitcoin() -> None:
    """Bitcoin detail should include name and price."""
    info = await coin_info("bitcoin")
    assert info is not None
    assert info["name"] == "Bitcoin"
    assert info["current_price_usd"] > 0


@pytest.mark.asyncio
async def test_coin_info_unknown() -> None:
    """Unknown coin should return None."""
    info = await coin_info("fake_coin_nonexistent_98765")
    assert info is None


@pytest.mark.asyncio
async def test_popular_coins_btc() -> None:
    """Bitcoin should be in the popular coins dict."""
    assert "bitcoin" in POPULAR_COINS
    assert POPULAR_COINS["bitcoin"] == "Bitcoin"


@pytest.mark.asyncio
async def test_get_price_eur() -> None:
    """Bitcoin price in EUR should return a price."""
    result = await get_price("bitcoin", "eur")
    assert result is not None
    assert result["currency"] == "EUR"
    assert result["price"] > 0