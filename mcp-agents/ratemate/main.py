"""CLI entry point for RateMate.

Usage:
  # MCP stdio mode (for Claude Desktop etc.)
  python main.py

  # HTTP SSE server
  python main.py --http --port 8080

  # Direct CLI
  python main.py convert 100 USD EUR
  python main.py convert 100 USD JPY --date 2024-01-01
  python main.py currencies
  python main.py rates USD
  python main.py crypto-price bitcoin
  python main.py crypto-price bitcoin --vs-currency eur
  python main.py crypto-top --limit 10
  python main.py crypto-info bitcoin
  python main.py historical USD EUR 2024-01-01 2024-12-31
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

load_dotenv()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RateMate — currency & crypto rates")
    parser.add_argument("--http", action="store_true", help="Run as HTTP/SSE server")
    parser.add_argument("--port", type=int, default=8080, help="HTTP server port")
    parser.add_argument("--simulate", action="store_true", help="Use simulated data (no API calls)")

    sub = parser.add_subparsers(dest="command")

    # convert
    c = sub.add_parser("convert", help="Convert fiat currency")
    c.add_argument("amount", type=float)
    c.add_argument("from_currency", nargs="?", default="USD")
    c.add_argument("to_currency", nargs="?", default="EUR")
    c.add_argument("--date", help="Historical date YYYY-MM-DD")

    # currencies
    sub.add_parser("currencies", help="List supported currencies")

    # rates
    r = sub.add_parser("rates", help="Latest exchange rates")
    r.add_argument("base", nargs="?", default="USD")

    # historical
    h = sub.add_parser("historical", help="Historical rate range")
    h.add_argument("from_currency", default="USD")
    h.add_argument("to_currency", default="EUR")
    h.add_argument("from_date")
    h.add_argument("to_date")

    # crypto-price
    cp = sub.add_parser("crypto-price", help="Get crypto price")
    cp.add_argument("coin_id", nargs="?", default="bitcoin")
    cp.add_argument("--vs-currency", default="usd")

    # crypto-top
    ct = sub.add_parser("crypto-top", help="Top cryptocurrencies")
    ct.add_argument("--limit", type=int, default=10)

    # crypto-info
    ci = sub.add_parser("crypto-info", help="Crypto details")
    ci.add_argument("coin_id", nargs="?", default="bitcoin")

    return parser


async def _run_cli(args: argparse.Namespace) -> None:
    """Run a single CLI command and print the result."""
    if args.simulate:
        print("[simulated mode — no real API calls]")

    cmd = args.command

    if cmd == "convert":
        from src.exchange import convert
        result = await convert(args.amount, args.from_currency.upper(), args.to_currency.upper(), args.date)
        if result:
            label = f"on {result['date']}" if result["date"] != "latest" else "latest"
            print(f"{result['amount']:,.2f} {result['from']} = {result['result']:,.2f} {result['to']} @ {result['rate']:.6f} ({label})")
        else:
            print(f"Could not convert {args.amount} {args.from_currency} → {args.to_currency}")

    elif cmd == "currencies":
        from src.exchange import list_currencies
        currencies = await list_currencies()
        if currencies:
            for code in sorted(currencies):
                print(f"  {code}: {currencies[code]}")
        else:
            print("Could not fetch currencies.")

    elif cmd == "rates":
        from src.exchange import latest_rates
        data = await latest_rates(args.base.upper())
        if data:
            print(f"Exchange rates (base: {data['base']}, {data['date']}):")
            for code in sorted(data["rates"]):
                print(f"  {code}: {data['rates'][code]:.6f}")
        else:
            print(f"Could not fetch rates for {args.base}.")

    elif cmd == "crypto-price":
        from src.crypto import get_price
        result = await get_price(args.coin_id.lower(), args.vs_currency.lower())
        if result:
            print(f"{result['coin'].title()}: {result['price']:,.2f} {result['currency']}")
        else:
            print(f"Coin '{args.coin_id}' not found.")

    elif cmd == "crypto-top":
        from src.crypto import get_top_coins
        coins = await get_top_coins(args.limit)
        if coins:
            print(f"Top {len(coins)} Cryptocurrencies:")
            for c in coins:
                change = f"{c['change_24h']:+.2f}%" if c.get("change_24h") is not None else "N/A"
                cap = f"${c['market_cap']:,.0f}" if c.get("market_cap") else "N/A"
                print(f"  #{c['rank']} {c['name']:>6s}  ${c['price']:>8,.2f}  {change}  cap={cap}")
        else:
            print("Could not fetch crypto data.")

    elif cmd == "crypto-info":
        from src.crypto import coin_info
        info = await coin_info(args.coin_id.lower())
        if info:
            print(f"{info['name']} ({info['symbol']})")
            if info.get("current_price_usd"):
                print(f"  Price: ${info['current_price_usd']:,.2f}")
            if info.get("market_cap_rank"):
                print(f"  Market Cap Rank: #{info['market_cap_rank']}")
            if info.get("price_change_24h_pct") is not None:
                print(f"  24h Change: {info['price_change_24h_pct']:+.2f}%")
            if info.get("high_24h_usd"):
                print(f"  24h High: ${info['high_24h_usd']:,.2f}")
            if info.get("low_24h_usd"):
                print(f"  24h Low: ${info['low_24h_usd']:,.2f}")
            if info.get("all_time_high_usd"):
                print(f"  All-Time High: ${info['all_time_high_usd']:,.2f}")
        else:
            print(f"Could not fetch info for '{args.coin_id}'.")

    elif cmd == "historical":
        from src.exchange import historical_range
        data = await historical_range(args.from_currency.upper(), args.to_currency.upper(), args.from_date, args.to_date)
        if data and data.get("rates"):
            for date_str in sorted(data["rates"].keys()):
                rate = data["rates"][date_str].get(args.to_currency.upper(), "?")
                print(f"  {date_str}: {rate}")
        else:
            print(f"Could not fetch historical data from {args.from_date} to {args.to_date}.")

    else:
        print("Unknown command. See --help.")


def main() -> None:
    """Entry point."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.http:
        # Run as HTTP SSE server
        import uvicorn
        uvicorn.run(
            "server:mcp.sse_app",
            host="0.0.0.0",
            port=args.port,
            reload=False,
            log_level="info",
        )
        return

    if args.command:
        import asyncio
        asyncio.run(_run_cli(args))
        return

    # Default: run MCP in stdio mode
    from server import mcp
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()