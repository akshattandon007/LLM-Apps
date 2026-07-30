"""
Product Extractor Agent — Fetches product details from a URL using web search.
"""

from .base import BaseAgent


SYSTEM_PROMPT = """You are a product intelligence agent. Your job is to extract precise product details from a given URL.

When given a product URL, use web search to:
1. Identify the product name, brand, model number, key specs, and category
2. Find the current listed price on that page
3. Identify the retailer/website

Return ONLY a JSON object with this exact schema (no markdown, no preamble):
{
  "product_name": "Full product name",
  "brand": "Brand name",
  "model": "Model number or variant",
  "category": "Product category (e.g. Laptop, Headphones, TV)",
  "specs": ["Key spec 1", "Key spec 2", "Key spec 3"],
  "original_price": "Price as shown (e.g. £299.99)",
  "original_currency": "GBP/USD/EUR etc",
  "original_retailer": "Retailer name",
  "search_query": "Optimised search query to find this product elsewhere (brand + model + key specs)"
}

Be precise. The search_query should be good enough to find this exact product on comparison sites.
"""


class ProductExtractorAgent(BaseAgent):
    """Extracts product details from a given URL."""

    def extract(self, url: str) -> dict:
        print("  🔍 [Product Extractor] Analysing product URL...")

        messages = [
            {
                "role": "user",
                "content": f"Extract all product details from this URL: {url}\n\nUse web search to retrieve the page and identify the product.",
            }
        ]

        response = self._call(
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=[self.web_search_tool],
        )

        # Agentic tool use loop — keep going until the model stops calling tools
        while response.stop_reason == "tool_use":
            # Collect all tool use blocks
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            # Append assistant message with full content
            messages.append({"role": "assistant", "content": response.content})

            # Build tool results for each tool call
            tool_results = []
            for block in tool_use_blocks:
                # The web search tool returns results in block.content when available
                search_content = ""
                if hasattr(block, "input") and block.input:
                    search_content = f"Search performed for: {block.input.get('query', '')}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": search_content or "Search completed successfully.",
                })

            messages.append({"role": "user", "content": tool_results})

            response = self._call(
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=[self.web_search_tool],
            )

        try:
            product = self._extract_json(response)
            print(f"  ✅ Found: {product.get('product_name', 'Unknown product')}")
            print(f"     Brand: {product.get('brand')} | Price: {product.get('original_price')}")
            return product
        except Exception as e:
            # If JSON parsing fails, ask the model to reformat its answer
            print(f"  🔄 Retrying with explicit JSON request...")
            messages.append({"role": "assistant", "content": self._extract_text(response)})
            messages.append({
                "role": "user",
                "content": "Now output ONLY the JSON object with the product details. No markdown, no explanation, just the raw JSON."
            })

            retry_response = self._call(
                system=SYSTEM_PROMPT,
                messages=messages,
            )

            try:
                product = self._extract_json(retry_response)
                print(f"  ✅ Found: {product.get('product_name', 'Unknown product')}")
                return product
            except Exception as e2:
                print(f"  ⚠️  Could not parse product details ({e2}), using fallback")
                text = self._extract_text(retry_response)
                return {
                    "product_name": "Unknown product",
                    "brand": "",
                    "model": "",
                    "category": "",
                    "specs": [],
                    "original_price": "Unknown",
                    "original_currency": "GBP",
                    "original_retailer": url,
                    "search_query": url,
                    "_raw": text,
                }
