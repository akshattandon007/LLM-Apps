# Flow — RateMate

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   MCP Host                            │
│  (Claude Desktop / Cursor / CLI)                     │
└──────────┬─────────────────────────────┬────────────┘
           │ stdio / SSE / CLI args      │
           ▼                             ▼
┌────────────────────┐   ┌────────────────────────────┐
│    server.py        │   │      main.py (CLI)         │
│  FastMCP instance   │   │  argparse → asyncio.run()  │
│  @mcp.tool() decor  │   │                            │
└────┬───────────────┘   └─────┬──────────────────────┘
     │                         │
     ▼                         ▼
┌─────────────────────────────────────────────────────┐
│                    src/ modules                       │
├─────────────────┬─────────────────┬─────────────────┤
│  src/exchange.py │ src/crypto.py   │  (future)        │
│  Frankfurter API  │ CoinGecko API   │                  │
└─────────────────┴─────────────────┴─────────────────┘
     │                         │
     ▼                         ▼
┌────────────┐   ┌────────────────────────┐
│ Frankfurter│   │     CoinGecko          │
│ (zero-auth)│   │  (free tier, no key)   │
└────────────┘   └────────────────────────┘
```

## Tool Call Chains

### `convert_currency(amount, from, to, date?)`

```
server.py:convert_currency()
  └─ src/exchange.py:convert(amount, from_currency, to_currency, date)
      └─ httpx.AsyncClient.get()
          ├─ GET /latest?from=USD&to=EUR     (no date)
          └─ GET /2024-01-01?from=USD&to=EUR (with date)
      └─ Parse response: rate * amount = result
  └─ Format: "{amount} {from} = {result} {to} @ {rate}"
```

### `list_supported_currencies()`

```
server.py:list_supported_currencies()
  └─ src/exchange.py:list_currencies()
      └─ httpx.AsyncClient.get()
          └─ GET /currencies
      └─ Parse: {"EUR": "Euro", "USD": "United States Dollar", ...}
  └─ Format: markdown table
```

### `latest_exchange_rates(base_currency)`

```
server.py:latest_exchange_rates()
  └─ src/exchange.py:latest_rates(from_currency)
      └─ httpx.AsyncClient.get()
          └─ GET /latest?from=USD
      └─ Parse: {base, date, rates: {EUR: 0.92, JPY: 150.2, ...}}
  └─ Format: sorted list with header
```

### `historical_rates(from, to, from_date, to_date)`

```
server.py:historical_rates()
  └─ src/exchange.py:historical_range(from, to, from_date, to_date)
      └─ httpx.AsyncClient.get()
          └─ GET /2024-01-01..2024-12-31?from=USD&to=EUR
      └─ Parse: rates keyed by date
  └─ Format: date → rate lines
```

### `crypto_price(coin_id, vs_currency)`

```
server.py:crypto_price()
  └─ src/crypto.py:get_price(coin_id, vs_currency)
      └─ httpx.AsyncClient.get()
          └─ GET /simple/price?ids=bitcoin&vs_currencies=usd
      └─ Parse: {bitcoin: {usd: 67000}}
  └─ Format: "{Coin}: ${price} USD"
```

### `top_cryptocurrencies(limit, vs_currency)`

```
server.py:top_cryptocurrencies()
  └─ src/crypto.py:get_top_coins(limit, vs_currency)
      └─ httpx.AsyncClient.get()
          └─ GET /coins/markets?vs_currency=usd&order=market_cap_desc&per_page=N
      └─ Parse: [{id, symbol, current_price, market_cap, price_change_percentage_24h}, ...]
  └─ Format: markdown table with rank/name/price/change/cap
```

### `crypto_details(coin_id)`

```
server.py:crypto_details()
  └─ src/crypto.py:coin_info(coin_id)
      └─ httpx.AsyncClient.get()
          └─ GET /coins/{coin_id}?localization=false&tickers=false&...
      └─ Parse: name, symbol, current_price, market_cap_rank, high_24h,
                low_24h, price_change_24h_pct, ath, description
  └─ Format: multi-line report
```

## CLI Entry Chain (main.py)

```
main.py:main()
  ├── --http flag → uvicorn.run("server:mcp.sse_app")
  ├── subcommand  → _run_cli(args) via asyncio.run()
  │    └── dispatches to matching src/ function
  │         └── prints formatted output
  └── no args    → mcp.run(transport="stdio")
```

## Data Flow

```
User: "How much is $100 in yen?"
  LLM calls convert_currency(100, "USD", "JPY")
    → server.py decorator receives typed args
    → src/exchange.py:convert() builds URL, sends GET
    → Frankfurter API returns {"amount": 100, "rate": 149.32, "result": 14932.0}
    → return formatted string
  LLM reads "100.00 USD = 14,932.00 JPY @ 149.320000 (latest rate)"
  LLM responds: "$100 is currently worth about ¥14,932."
```

## Module Dependency Graph

```
main.py
  ├── server.py (imports src module funcs)
  │    ├── src/exchange.py
  │    │    └── httpx
  │    └── src/crypto.py
  │         └── httpx
  └── dotenv (for .env loading, not required)

tests/test_exchange.py
  └── src/exchange.py

tests/test_crypto.py
  └── src/crypto.py
```