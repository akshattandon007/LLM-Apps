"""
Promo Code Agent — Finds the best promo codes, discounts and offers.
This agent is conversational and can ask follow-up questions.
"""

from .base import BaseAgent


SYSTEM_PROMPT = """You are an expert promo code hunter and deals specialist. Your mission is to find every possible discount for a specific product at a specific retailer.

You search for:
1. Active promo/coupon codes for the retailer
2. Cashback offers (Quidco, TopCashback, Rakuten, etc.)
3. Student/NHS/military discounts
4. Credit card or bank offers
5. Newsletter signup discounts
6. Loyalty programme benefits
7. Bundle deals or trade-in offers
8. Seasonal sales or upcoming sales events

For each discount found, provide:
- The code (if applicable)
- Discount amount/percentage
- Exact redemption steps
- Expiry date if known
- Stacking possibilities (can it be combined with other offers?)

You are conversational. If you need clarification to find better deals (e.g., whether they have a student email, which bank they use, whether they're a new customer), ASK. Keep questions brief and helpful.

When presenting results, be specific and actionable. Include the total price after all discounts.

Format your final response clearly with sections:
🎟️ PROMO CODES
💸 CASHBACK OFFERS  
🎓 SPECIAL DISCOUNTS
📋 REDEMPTION STEPS
💡 PRO TIPS
"""


class PromoCodeAgent(BaseAgent):
    """Conversational agent that finds promo codes and guides redemption."""

    def __init__(self):
        super().__init__()
        self.conversation_history = []

    def find_promos(self, product: dict, price_data: dict) -> None:
        """Start the promo code search and enter a conversational loop."""
        retailer = price_data.get("cheapest_retailer", {})
        retailer_name = retailer.get("name", "the retailer")
        product_name = product.get("product_name", "the product")
        price = retailer.get("price", "unknown price")

        print(f"\n  🎟️  [Promo Code Agent] Hunting for discount codes...")
        print(f"     Retailer: {retailer_name} | Price: {price}\n")

        initial_prompt = f"""Find all available promo codes, discounts, and cashback offers for:

Product: {product_name}
Retailer: {retailer_name}
Retailer URL: {retailer.get('url', '')}
Current price: {price}
Category: {product.get('category', '')}

Search for:
1. Active coupon/promo codes for {retailer_name}
2. Cashback portals offering cashback at {retailer_name}
3. Any special discounts (student, NHS, new customer etc.)
4. Credit card or bank offers at {retailer_name}
5. Any upcoming sales events

Be thorough. Then ask me 1-2 targeted follow-up questions to uncover more savings.
"""

        self.conversation_history = [{"role": "user", "content": initial_prompt}]

        # First search
        response = self._call(
            system=SYSTEM_PROMPT,
            messages=self.conversation_history,
            tools=[self.web_search_tool],
        )

        # Handle tool use
        while response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Search completed.",
                    })

            self.conversation_history.append(
                {"role": "assistant", "content": response.content}
            )
            self.conversation_history.append(
                {"role": "user", "content": tool_results}
            )

            response = self._call(
                system=SYSTEM_PROMPT,
                messages=self.conversation_history,
                tools=[self.web_search_tool],
            )

        # Show first results
        agent_text = self._extract_text(response)
        self.conversation_history.append(
            {"role": "assistant", "content": agent_text}
        )

        print("─" * 60)
        print(agent_text)
        print("─" * 60)

        # Conversational follow-up loop
        self._conversation_loop()

    def _conversation_loop(self):
        """Allow the user to ask follow-up questions."""
        print("\n  💬 Ask follow-up questions or type 'done' to finish.\n")

        while True:
            user_input = input("  You: ").strip()

            if not user_input or user_input.lower() in {"done", "exit", "quit", "q"}:
                print("\n  ✅ Promo code search complete. Good luck saving!\n")
                break

            self.conversation_history.append(
                {"role": "user", "content": user_input}
            )

            response = self._call(
                system=SYSTEM_PROMPT,
                messages=self.conversation_history,
                tools=[self.web_search_tool],
            )

            # Handle tool use
            while response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Search completed.",
                        })

                self.conversation_history.append(
                    {"role": "assistant", "content": response.content}
                )
                self.conversation_history.append(
                    {"role": "user", "content": tool_results}
                )

                response = self._call(
                    system=SYSTEM_PROMPT,
                    messages=self.conversation_history,
                    tools=[self.web_search_tool],
                )

            agent_reply = self._extract_text(response)
            self.conversation_history.append(
                {"role": "assistant", "content": agent_reply}
            )

            print(f"\n  Agent: {agent_reply}\n")
            print("─" * 60)
