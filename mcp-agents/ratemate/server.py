"""RateMate MCP Server — currency exchange + crypto price tools.

Lets you convert between 32 fiat currencies (Frankfurter, zero-auth) and
check crypto prices (CoinGecko, free tier).  No API keys required.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

from src.exchange import (
    convert as _convert_fiat,
    latest_rates,
    list_currencies as _list_currencies,
    historical_range as _historical_range,
)
from src.crypto import (
    get_price as _crypto_price,
    get_top_coins as _top_coins,
    coin_info as _coin_info,
    POPULAR_COINS,
)

mcp = FastMCP(
    "RateMate",
    description="Currency exchange & crypto price tool. Convert between 32 fiat currencies (no API key) and check cryptocurrency prices (CoinGecko free tier).",
)


@mcp.tool()
async def convert_currency(
    amount: float,
    from_currency: str = "USD",
    to_currency: str = "EUR",
    date: str | None = None,
) -> str:
    """Convert an amount from one currency to another.

    Supports 32 fiat currencies (EUR, GBP, JPY, USD, etc.).  Optionally
    specify a historical *date* (YYYY-MM-DD) for past exchange rates.

    Args:
        amount: The amount to convert (e.g. 100).
        from_currency: Three-letter currency code to convert FROM (default USD).
        to_currency: Three-letter currency code to convert TO (default EUR).
        date: Optional historical rate date in YYYY-MM-DD format.
    """
    result = await _convert_fiat(amount, from_currency.upper(), to_currency.upper(), date)
    if result is None:
        return f"Could not convert {amount} {from_currency} → {to_currency}. Check the currency codes (e.g. EUR, GBP, JPY)."
    label = f"on {result['date']}" if result["date"] != "latest" else "(latest rate)"
    return (
        f"{result['amount']:,.2f} {result['from']} = **{result['result']:,.2f} {result['to']}** "
        f"@ {result['rate']:.6f} {label}"
    )


@mcp.tool()
async def list_supported_currencies() -> str:
    """List all 32 supported fiat currencies with their full names.

    Returns a formatted table of currency codes and descriptions.
    """
    currencies = await _list_currencies()
    if currencies is None:
        return "Could not fetch currency list. The API may be temporarily unavailable."
    lines = ["| Code | Name |", "|------|------|"]
    for code in sorted(currencies):
        lines.append(f"| {code} | {currencies[code]} |")
    return "## Supported Currencies\n\n" + "\n".join(lines)


@mcp.tool()
async def latest_exchange_rates(base_currency: str = "USD") -> str:
    """Get all latest exchange rates relative to a base currency.

    Args:
        base_currency: Three-letter currency code (default USD).
    """
    rates = await latest_rates(base_currency.upper())
    if rates is None:
        return f"Could not fetch rates for {base_currency}."
    lines = [f"## Exchange Rates (base: {rates['base']}, as of {rates['date']})", ""]
    for code in sorted(rates["rates"]):
        lines.append(f"  {code}: {rates['rates'][code]:.6f}")
    return "\n".join(lines)


@mcp.tool()
async def historical_rates(
    from_currency: str = "USD",
    to_currency: str = "EUR",
    from_date: str = "",
    to_date: str = "",
) -> str:
    """Get exchange rate history between two dates.

    Args:
        from_currency: Base currency code (default USD).
        to_currency: Target currency code (default EUR).
        from_date: Start date in YYYY-MM-DD format (required).
        to_date: End date in YYYY-MM-DD format (required).
    """
    if not from_date or not to_date:
        return "Both from_date and to_date are required (YYYY-MM-DD format)."
    data = await _historical_range(from_currency.upper(), to_currency.upper(), from_date, to_date)
    if data is None:
        return f"Could not fetch historical rates from {from_date} to {to_date}."
    rates = data.get("rates", {})
    lines = [
        f"## {from_currency.upper()} → {to_currency.upper()} ({from_date} → {to_date})",
        "",
    ]
    for date_str in sorted(rates.keys()):
        rate = rates[date_str].get(to_currency.upper(), "?")
        lines.append(f"  {date_str}: {rate}")
    return "\n".join(lines)


@mcp.tool()
async def crypto_price(coin_id: str = "bitcoin", vs_currency: str = "usd") -> str:
    """Get the current price of a cryptocurrency in your chosen currency.

    Popular coin IDs: bitcoin, ethereum, solana, cardano, dogecoin, chainlink,
    polkadot, avalanche-2, ripple, tether.

    Args:
        coin_id: CoinGecko coin ID (e.g. 'bitcoin', 'ethereum', 'solana').
        vs_currency: Three-letter currency code (default 'usd').
    """
    result = await _crypto_price(coin_id.lower(), vs_currency.lower())
    if result is None:
        popular = ", ".join(f"`{k}`" for k in POPULAR_COINS)
        return f"Coin '{coin_id}' not found. Popular IDs: {popular}"
    return f"**{result['coin'].title()}**: {result['price']:,.2f} {result['currency']}"


@mcp.tool()
async def top_cryptocurrencies(limit: int = 10, vs_currency: str = "usd") -> str:
    """List the top cryptocurrencies by market capitalisation.

    Args:
        limit: How many to show (max 50, default 10).
        vs_currency: Currency to show prices in (default 'usd').
    """
    coins = await _top_coins(limit, vs_currency.lower())
    if coins is None:
        return "Could not fetch crypto market data."
    lines = [
        f"## Top {len(coins)} Cryptocurrencies (in {vs_currency.upper()})",
        "",
        "| # | Coin | Price | 24h Δ | Market Cap |",
        "|---|------|-------|-------|------------|",
    ]
    for c in coins:
        change = f"{c['change_24h']:+.2f}%" if c.get("change_24h") is not None else "N/A"
        cap = f"${c['market_cap']:,.0f}" if c.get("market_cap") else "N/A"
        lines.append(f"| {c['rank']} | {c['name']:>6s} | ${c['price']:>8,.2f} | {change:>8s} | {cap} |")
    return "\n".join(lines)


@mcp.tool()
async def crypto_details(coin_id: str = "bitcoin") -> str:
    """Get detailed information about a specific cryptocurrency.

    Args:
        coin_id: CoinGecko coin ID (e.g. 'bitcoin', 'ethereum', 'solana').
    """
    info = await _coin_info(coin_id.lower())
    if info is None:
        return f"Coin '{coin_id}' not found or API rate-limited. Try one of: {', '.join(POPULAR_COINS)}"
    lines = [
        f"## {info['name']} ({info['symbol']})",
        "",
        f"**Current Price:** ${info['current_price_usd']:,.2f}" if info.get("current_price_usd") else "",
        f"**Market Cap Rank:** #{info['market_cap_rank']}" if info.get("market_cap_rank") else "",
        f"**24h Price Change:** {info['price_change_24h_pct']:+.2f}%" if info.get("price_change_24h_pct") is not None else "",
        f"**24h High:** ${info['high_24h_usd']:,.2f}" if info.get("high_24h_usd") else "",
        f"**24h Low:** ${info['low_24h_usd']:,.2f}" if info.get("low_24h_usd") else "",
        f"**24h Volume:** ${info['total_volume_usd']:,.0f}" if info.get("total_volume_usd") else "",
        f"**All-Time High:** ${info['all_time_high_usd']:,.2f}" if info.get("all_time_high_usd") else "",
        "",
    ]
    if info.get("description"):
        lines.append(f"_{info['description'][:300]}..._")
    return "\n".join(l for l in lines if l)