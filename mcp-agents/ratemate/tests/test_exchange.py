"""Tests for exchange-rate module — verify API calls and logic."""

from __future__ import annotations

import pytest
import pytest_asyncio

from src.exchange import convert, latest_rates, list_currencies, historical_range


@pytest.mark.asyncio
async def test_latest_rates_default() -> None:
    """Fetching latest USD rates should return rates dict with EUR."""
    result = await latest_rates("USD")
    assert result is not None
    assert result["base"] == "USD"
    assert "EUR" in result["rates"]
    assert "JPY" in result["rates"]


@pytest.mark.asyncio
async def test_latest_rates_eur_base() -> None:
    """Fetching latest EUR rates should work too."""
    result = await latest_rates("EUR")
    assert result is not None
    assert result["base"] == "EUR"
    assert "USD" in result["rates"]


@pytest.mark.asyncio
async def test_convert_usd_eur() -> None:
    """Convert 100 USD to EUR should give a positive result."""
    result = await convert(100, "USD", "EUR")
    assert result is not None
    assert result["amount"] == 100
    assert result["from"] == "USD"
    assert result["to"] == "EUR"
    assert result["result"] > 0
    assert result["rate"] > 0


@pytest.mark.asyncio
async def test_convert_usd_jpy() -> None:
    """Convert 50 USD to JPY — should return a large number (JPY is ~150/USD)."""
    result = await convert(50, "USD", "JPY")
    assert result is not None
    assert result["result"] > 1000  # 50 USD in JPY should be thousands
    assert result["rate"] > 50


@pytest.mark.asyncio
async def test_convert_unknown_currency() -> None:
    """Unknown currency code should return None."""
    result = await convert(100, "USD", "XYZ")
    assert result is None


@pytest.mark.asyncio
async def test_list_currencies() -> None:
    """Currency listing should include major currencies."""
    currencies = await list_currencies()
    assert currencies is not None
    assert "USD" in currencies
    assert "EUR" in currencies
    assert "JPY" in currencies
    assert "GBP" in currencies


@pytest.mark.asyncio
async def test_historical_range() -> None:
    """Historical range between two dates should return rate list."""
    result = await historical_range("USD", "EUR", "2024-01-01", "2024-01-31")
    assert result is not None
    assert "rates" in result
    assert len(result["rates"]) > 0
    # At least a few days in January
    assert any("2024-01-" in d for d in result["rates"])


@pytest.mark.asyncio
async def test_convert_eur_usd() -> None:
    """Convert 100 EUR to USD should work (reverse direction)."""
    result = await convert(100, "EUR", "USD")
    assert result is not None
    assert result["result"] > 0
    assert result["rate"] > 0


@pytest.mark.asyncio
async def test_convert_with_date() -> None:
    """Historical conversion with a specific date."""
    result = await convert(100, "USD", "EUR", date="2024-06-03")
    assert result is not None
    assert result["date"] == "2024-06-03"