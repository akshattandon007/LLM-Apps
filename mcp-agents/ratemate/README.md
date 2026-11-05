# RateMate — Free Exchange Rate & Crypto Price MCP

**RateMate** is an MCP server that converts between 32 fiat currencies and checks
cryptocurrency prices — no API keys required.

## What it does

- **Convert currency** — "How much is $100 in euros?" → instant conversion with
  live or historical rates
- **List exchange rates** — See all 32 currencies at a glance
- **Historical rates** — Track exchange-rate trends between any two dates  
- **Crypto prices** — Check Bitcoin, Ethereum, Solana, Dogecoin, and 100+ more
- **Top coins** — See the crypto market leaders ranked by market cap
- **Coin details** — Deep dive into any coin: 24h high/low, ATH, volume

## Powered by

| API | Auth | Tier |
|-----|------|------|
| [Frankfurter](https://api.frankfurter.app) | None | Free, unlimited |
| [CoinGecko](https://www.coingecko.com/en/api) | None | Free, 10-30 req/min |

## Install

```bash
cd mcp-agents/ratemate
pip install -r requirements.txt
```

## Usage

### MCP mode (for Claude Desktop, Cursor, etc.)

```bash
python main.py
```

### HTTP/SSE server

```bash
python main.py --http --port 8080
```

### CLI commands

```bash
# Convert 100 USD to Euros
python main.py convert 100 USD EUR

# Convert 50 USD to JPY using historical rate
python main.py convert 50 USD JPY --date 2024-06-01

# List all supported currencies
python main.py currencies

# Latest exchange rates (base: USD)
python main.py rates USD

# Historical rate range
python main.py historical USD JPY 2024-01-01 2024-12-31

# Bitcoin price in USD
python main.py crypto-price bitcoin

# Bitcoin price in EUR
python main.py crypto-price bitcoin --vs-currency eur

# Top 15 cryptocurrencies
python main.py crypto-top --limit 15

# Detailed coin info
python main.py crypto-info ethereum
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `convert_currency` | Convert amount between any two of 32 fiat currencies (live or historical date) |
| `list_supported_currencies` | Show all 32 currency codes with full names |
| `latest_exchange_rates` | All exchange rates relative to a base currency |
| `historical_rates` | Rate history between two dates for any currency pair |
| `crypto_price` | Current price of any cryptocurrency |
| `top_cryptocurrencies` | Top N coins by market cap with 24h change |
| `crypto_details` | Detailed info for one coin (ATH, volume, description) |

## Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

Tests hit the live APIs (Frankfurter + CoinGecko) to verify real output. Both
are free and require no auth — tests should pass if you have internet access.