"""
Price Comparison Agent — Searches the internet for the best price on a product.
"""

from .base import BaseAgent


SYSTEM_PROMPT = """You are a price comparison expert. Your job is to find the cheapest legitimate retailer selling a specific product.

Given product details, use web search to:
1. Search for the product on multiple retailers and price comparison sites
2. Check sites like Google Shopping, PriceRunner, PriceSpy, CamelCamelCamel (for Amazon), Idealo, and major retailers
3. Compare prices including delivery costs where visible
4. Identify the top 5 cheapest options

Return ONLY a JSON object with this schema (no markdown, no preamble):
{
  "cheapest_retailer": {
    "name": "Retailer name",
    "url": "Direct product URL",
    "price": "Price with currency symbol",
    "price_numeric": 0.00,
    "currency": "GBP/USD/EUR",
    "delivery": "Delivery cost or 'Free'",
    "total_price": "Price + delivery",
    "total_numeric": 0.00,
    "in_stock": true
  },
  "alternatives": [
    {
      "name": "Retailer name",
      "url": "URL",
      "price": "Price",
      "price_numeric": 0.00,
      "delivery": "Delivery info",
      "total_numeric": 0.00
    }
  ],
  "savings_vs_original": "How much cheaper than original (e.g. '£45 cheaper')",
  "notes": "Any important notes (e.g. refurbished, different variant, etc.)"
}

Always verify you're comparing the exact same product variant. Flag any differences.
Sort alternatives by total_numeric ascending.
"""


class PriceComparisonAgent(BaseAgent):
    """Finds the cheapest price for a product across the internet."""

    def find_best_price(self, product: dict) -> dict:
        product_name = product.get("product_name", "Unknown")
        search_query = product.get("search_query", product_name)
        original_price = product.get("original_price", "unknown")

        print(f"\n  💰 [Price Comparison] Searching for best price...")
        print(f"     Query: {search_query}")

        prompt = f"""Find the cheapest price for this product:

Product: {product_name}
Brand: {product.get('brand')}
Model: {product.get('model')}
Specs: {', '.join(product.get('specs', []))}
Original price: {original_price} at {product.get('original_retailer')}
Search query: {search_query}

Search for this product across multiple retailers and price comparison sites.
Find at least 3-5 different prices. Include UK retailers if the currency is GBP.
"""

        messages = [{"role": "user", "content": prompt}]

        response = self._call(
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=[self.web_search_tool],
        )

        # Agentic tool use loop
        while response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in tool_use_blocks:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Search completed successfully.",
                })

            messages.append({"role": "user", "content": tool_results})

            response = self._call(
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=[self.web_search_tool],
            )

        try:
            result = self._extract_json(response)
            cheapest = result.get("cheapest_retailer", {})
            print(f"  ✅ Cheapest: {cheapest.get('name')} — {cheapest.get('price')}")
            print(f"     Savings: {result.get('savings_vs_original', 'unknown')}")
            return result
        except Exception as e:
            # Retry with explicit JSON request
            print(f"  🔄 Retrying JSON extraction...")
            messages.append({"role": "assistant", "content": self._extract_text(response)})
            messages.append({
                "role": "user",
                "content": "Now output ONLY the JSON object. No markdown, no explanation, just raw JSON."
            })
            retry = self._call(system=SYSTEM_PROMPT, messages=messages)
            try:
                return self._extract_json(retry)
            except Exception:
                return {
                    "cheapest_retailer": {
                        "name": "See notes",
                        "url": "",
                        "price": "Unknown",
                        "price_numeric": 0,
                        "currency": "GBP",
                        "delivery": "Unknown",
                        "total_price": "Unknown",
                        "total_numeric": 0,
                        "in_stock": True,
                    },
                    "alternatives": [],
                    "savings_vs_original": "Unknown",
                    "notes": self._extract_text(retry),
                }
