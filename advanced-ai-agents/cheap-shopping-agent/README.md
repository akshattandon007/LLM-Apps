# 🛍️ Promo Code Agent

A multi-agent AI system that finds the **cheapest price** and **best promo codes** for any product — just give it a URL.

Built with [Claude](https://www.anthropic.com/claude) + web search. Three specialised agents work in sequence to extract product details, compare prices across the internet, and hunt down every available discount.

---

## How It Works

```
You give a URL
     │
     ▼
┌─────────────────────┐
│  Product Extractor  │  Identifies product name, brand, model, specs & price
│       Agent         │  using web search on the URL
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Price Comparison   │  Searches Google Shopping, PriceRunner, Idealo,
│       Agent         │  CamelCamelCamel & major retailers for cheapest price
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Promo Code Agent  │  Finds active codes, cashback portals, student/NHS
│  (conversational)   │  discounts, credit card offers, and upcoming sales.
└─────────────────────┘  Asks you follow-up questions to unlock more savings.
```

---

## Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/yourname/promo-agent.git
cd promo-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...
```

> Get an API key at [console.anthropic.com](https://console.anthropic.com)

### 4. Run

```bash
# Pass URL as argument
python main.py https://www.amazon.co.uk/dp/B09XS7JWHH

# Or run interactively
python main.py
```

---

## Example Session

```
═══════════════════════════════════════════════════════════
  🛍️  PROMO CODE AGENT — Find the Best Deals
═══════════════════════════════════════════════════════════
  Powered by Claude AI + Web Search
═══════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────┐
│  STEP 1: Extract Product Details                         │
└──────────────────────────────────────────────────────────┘

  🔍 [Product Extractor] Analysing product URL...
  ✅ Found: Sony WH-1000XM5 Wireless Headphones
     Brand: Sony | Price: £279.00

  📦 Product Summary:
     Name:     Sony WH-1000XM5 Wireless Headphones
     Brand:    Sony
     Model:    WH-1000XM5
     Category: Over-ear Headphones
     Specs:    ANC | 30hr battery | Bluetooth 5.2
     Price:    £279.00 @ Amazon UK

┌──────────────────────────────────────────────────────────┐
│  STEP 2: Find Best Price Across the Web                  │
└──────────────────────────────────────────────────────────┘

  💰 [Price Comparison] Searching for best price...
  ✅ Cheapest: John Lewis — £249.00
     Savings: £30 cheaper than Amazon

  🏆 Best Price Found:
     Retailer: John Lewis
     Price:    £249.00
     Delivery: Free
     Total:    £249.00

  📊 Other Options:
     • Currys: £259.00 (delivery: Free)
     • Very: £265.00 (delivery: Free)
     • Amazon: £279.00 (delivery: Free with Prime)

┌──────────────────────────────────────────────────────────┐
│  STEP 3: Find Promo Codes & Deals                        │
└──────────────────────────────────────────────────────────┘

  🎟️  [Promo Code Agent] Hunting for discount codes...

────────────────────────────────────────────────────────────
🎟️ PROMO CODES
• SAVE10 — 10% off at John Lewis (unverified, worth trying)
• WELCOME15 — 15% off for new customers (expired but sometimes works)

💸 CASHBACK OFFERS
• TopCashback: 3.5% cashback at John Lewis → saves ~£8.72
• Quidco: 2.8% cashback → saves ~£6.97

🎓 SPECIAL DISCOUNTS
• John Lewis Student: 10% off with valid student email via TOTUM/UNiDAYS

📋 REDEMPTION STEPS
1. Go via TopCashback → click through to John Lewis
2. Add Sony WH-1000XM5 to cart
3. Apply code SAVE10 at checkout
4. Pay with an Amex card for potential additional 5% MR points

💡 PRO TIPS
• John Lewis price-matches Amazon — if Amazon drops below £249, they'll match it
• Check back on Black Friday for potential 20%+ discount

────────────────────────────────────────────────────────────

  💬 Ask follow-up questions or type 'done' to finish.

  You: Do I have a student email? Yes, I'm at UCL
  Agent: Great! With your UCL student email you can get 10% off at John Lewis
  via UNiDAYS. Here's exactly how...
```

---

## Project Structure

```
promo-agent/
├── main.py                    # Entry point
├── requirements.txt
├── .env.example
├── agents/
│   ├── __init__.py
│   ├── base.py                # Shared Anthropic client + helpers
│   ├── orchestrator.py        # Coordinates all agents
│   ├── product_extractor.py   # Extracts product details from URL
│   ├── price_comparison.py    # Finds cheapest price across web
│   └── promo_code.py          # Finds promo codes (conversational)
├── tests/
│   ├── __init__.py
│   └── test_agents.py         # Unit tests with mocking
└── README.md
```

---

## Agents

### `ProductExtractorAgent`
Uses Claude + web search to visit the product URL and extract structured data: name, brand, model, specs, price, and an optimised search query for finding the product elsewhere.

### `PriceComparisonAgent`
Takes the product details and searches across multiple retailers and price comparison sites (Google Shopping, PriceRunner, Idealo, CamelCamelCamel, etc.) to find the cheapest total price including delivery.

### `PromoCodeAgent`
A conversational agent that:
- Searches for active promo/coupon codes
- Checks cashback portals (TopCashback, Quidco, Rakuten)
- Looks up student, NHS, and military discounts
- Checks credit card and bank offers
- Identifies upcoming sales events
- **Asks you follow-up questions** to personalise results (e.g. student status, bank account, new/existing customer)

### `OrchestratorAgent`
Runs the three agents in sequence and presents results clearly. Async-compatible.

---

## Running Tests

```bash
python -m pytest tests/ -v

# Or with unittest
python -m unittest tests.test_agents -v
```

All tests mock the Anthropic API — no API calls are made during testing.

---

## Configuration

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required) |

All agents use `claude-sonnet-4-20250514` with the `web_search_20250305` tool.

---

## Requirements

- Python 3.9+
- `anthropic>=0.40.0`
- `python-dotenv>=1.0.0`

---

## Extending

To add a new agent (e.g. a warranty comparison agent):

1. Create `agents/warranty.py` subclassing `BaseAgent`
2. Define a `SYSTEM_PROMPT` and a main method
3. Import and call it from `agents/orchestrator.py`

---

## License

MIT
