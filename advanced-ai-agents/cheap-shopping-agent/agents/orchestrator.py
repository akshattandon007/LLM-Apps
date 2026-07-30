"""
Orchestrator Agent — Coordinates all sub-agents in sequence.
"""

from .product_extractor import ProductExtractorAgent
from .price_comparison import PriceComparisonAgent
from .promo_code import PromoCodeAgent


class OrchestratorAgent:
    """Coordinates the product extractor, price comparison, and promo code agents."""

    def __init__(self):
        self.product_extractor = ProductExtractorAgent()
        self.price_comparison = PriceComparisonAgent()
        self.promo_code = PromoCodeAgent()

    async def run(self, url: str) -> None:
        """Run the full pipeline for a given product URL."""

        print("\n" + "┌" + "─" * 58 + "┐")
        print("│  STEP 1: Extract Product Details" + " " * 25 + "│")
        print("└" + "─" * 58 + "┘\n")

        # Step 1: Extract product details
        product = self.product_extractor.extract(url)
        self._print_product_summary(product)

        print("\n" + "┌" + "─" * 58 + "┐")
        print("│  STEP 2: Find Best Price Across the Web" + " " * 18 + "│")
        print("└" + "─" * 58 + "┘\n")

        # Step 2: Find the best price
        price_data = self.price_comparison.find_best_price(product)
        self._print_price_summary(price_data)

        print("\n" + "┌" + "─" * 58 + "┐")
        print("│  STEP 3: Find Promo Codes & Deals" + " " * 23 + "│")
        print("└" + "─" * 58 + "┘\n")

        # Step 3: Find promo codes (conversational)
        self.promo_code.find_promos(product, price_data)

    def _print_product_summary(self, product: dict) -> None:
        print("\n  📦 Product Summary:")
        print(f"     Name:     {product.get('product_name')}")
        print(f"     Brand:    {product.get('brand')}")
        print(f"     Model:    {product.get('model')}")
        print(f"     Category: {product.get('category')}")
        specs = product.get("specs", [])
        if specs:
            print(f"     Specs:    {' | '.join(specs[:3])}")
        print(f"     Price:    {product.get('original_price')} @ {product.get('original_retailer')}")

    def _print_price_summary(self, price_data: dict) -> None:
        cheapest = price_data.get("cheapest_retailer", {})
        alternatives = price_data.get("alternatives", [])

        print("\n  🏆 Best Price Found:")
        print(f"     Retailer: {cheapest.get('name')}")
        print(f"     Price:    {cheapest.get('price')}")
        print(f"     Delivery: {cheapest.get('delivery', 'Unknown')}")
        print(f"     Total:    {cheapest.get('total_price', cheapest.get('price'))}")
        print(f"     Savings:  {price_data.get('savings_vs_original', 'Unknown')}")

        if alternatives:
            print("\n  📊 Other Options:")
            for alt in alternatives[:4]:
                print(f"     • {alt.get('name')}: {alt.get('price')} (delivery: {alt.get('delivery', '?')})")

        if price_data.get("notes"):
            print(f"\n  📝 Notes: {price_data.get('notes')}")
