#!/usr/bin/env python3
"""
Promo Code Agent - Find the best deals and promo codes for any product.
"""

import asyncio
import sys
from agents.orchestrator import OrchestratorAgent


async def main():
    print("\n" + "═" * 60)
    print("  🛍️  PROMO CODE AGENT — Find the Best Deals")
    print("═" * 60)
    print("  Powered by Claude AI + Web Search")
    print("═" * 60 + "\n")

    orchestrator = OrchestratorAgent()

    if len(sys.argv) > 1:
        product_url = sys.argv[1]
        print(f"  Product URL: {product_url}\n")
        await orchestrator.run(product_url)
    else:
        print("  Enter a product URL to find the best deals.")
        print("  Example: python main.py https://www.amazon.co.uk/dp/B09ABC123\n")
        product_url = input("  🔗 Product URL: ").strip()
        if product_url:
            await orchestrator.run(product_url)
        else:
            print("\n  ❌ No URL provided. Exiting.")


if __name__ == "__main__":
    asyncio.run(main())
