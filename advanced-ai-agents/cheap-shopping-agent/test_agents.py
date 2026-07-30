"""
Tests for the Promo Code Agent system.
Uses mocking to avoid real API calls during testing.
"""

import json
import unittest
from unittest.mock import MagicMock, patch


class TestProductExtractor(unittest.TestCase):
    """Tests for ProductExtractorAgent."""

    def _make_mock_response(self, content_dict: dict):
        """Create a mock Anthropic response with JSON content."""
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps(content_dict)

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.stop_reason = "end_turn"
        return mock_response

    @patch("agents.product_extractor.ProductExtractorAgent._call")
    def test_extract_returns_product_dict(self, mock_call):
        """Test that extract() returns a properly structured product dict."""
        from agents.product_extractor import ProductExtractorAgent

        expected = {
            "product_name": "Sony WH-1000XM5 Headphones",
            "brand": "Sony",
            "model": "WH-1000XM5",
            "category": "Headphones",
            "specs": ["ANC", "30hr battery", "Bluetooth 5.2"],
            "original_price": "£279.00",
            "original_currency": "GBP",
            "original_retailer": "Amazon UK",
            "search_query": "Sony WH-1000XM5 headphones ANC",
        }

        mock_call.return_value = self._make_mock_response(expected)

        agent = ProductExtractorAgent()
        result = agent.extract("https://amazon.co.uk/dp/B09XS7JWHH")

        self.assertEqual(result["product_name"], "Sony WH-1000XM5 Headphones")
        self.assertEqual(result["brand"], "Sony")
        self.assertEqual(result["original_price"], "£279.00")
        mock_call.assert_called_once()

    @patch("agents.product_extractor.ProductExtractorAgent._call")
    def test_extract_handles_json_parse_failure(self, mock_call):
        """Test graceful fallback when JSON parsing fails."""
        from agents.product_extractor import ProductExtractorAgent

        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Unable to parse this product"

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.stop_reason = "end_turn"

        mock_call.return_value = mock_response

        agent = ProductExtractorAgent()
        result = agent.extract("https://example.com/product")

        self.assertIn("product_name", result)
        self.assertIn("_raw", result)


class TestPriceComparison(unittest.TestCase):
    """Tests for PriceComparisonAgent."""

    def _make_mock_response(self, content_dict: dict):
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps(content_dict)

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.stop_reason = "end_turn"
        return mock_response

    @patch("agents.price_comparison.PriceComparisonAgent._call")
    def test_find_best_price_returns_cheapest(self, mock_call):
        """Test that find_best_price() returns cheapest retailer info."""
        from agents.price_comparison import PriceComparisonAgent

        expected = {
            "cheapest_retailer": {
                "name": "John Lewis",
                "url": "https://johnlewis.com/product/123",
                "price": "£249.00",
                "price_numeric": 249.00,
                "currency": "GBP",
                "delivery": "Free",
                "total_price": "£249.00",
                "total_numeric": 249.00,
                "in_stock": True,
            },
            "alternatives": [
                {
                    "name": "Currys",
                    "url": "https://currys.co.uk",
                    "price": "£259.00",
                    "price_numeric": 259.00,
                    "delivery": "Free",
                    "total_numeric": 259.00,
                }
            ],
            "savings_vs_original": "£30 cheaper",
            "notes": "",
        }

        mock_call.return_value = self._make_mock_response(expected)

        agent = PriceComparisonAgent()
        product = {
            "product_name": "Sony WH-1000XM5",
            "brand": "Sony",
            "model": "WH-1000XM5",
            "specs": ["ANC"],
            "original_price": "£279.00",
            "original_retailer": "Amazon",
            "search_query": "Sony WH-1000XM5",
            "category": "Headphones",
        }

        result = agent.find_best_price(product)

        self.assertEqual(result["cheapest_retailer"]["name"], "John Lewis")
        self.assertEqual(result["cheapest_retailer"]["price_numeric"], 249.00)
        self.assertEqual(result["savings_vs_original"], "£30 cheaper")


class TestOrchestrator(unittest.TestCase):
    """Tests for OrchestratorAgent."""

    @patch("agents.orchestrator.PromoCodeAgent")
    @patch("agents.orchestrator.PriceComparisonAgent")
    @patch("agents.orchestrator.ProductExtractorAgent")
    def test_orchestrator_calls_all_agents(
        self, MockExtractor, MockPricer, MockPromo
    ):
        """Test that the orchestrator calls all three sub-agents in order."""
        import asyncio
        from agents.orchestrator import OrchestratorAgent

        mock_product = {
            "product_name": "Test Product",
            "brand": "TestBrand",
            "model": "T1",
            "category": "Electronics",
            "specs": [],
            "original_price": "£100",
            "original_retailer": "TestShop",
            "search_query": "TestBrand T1",
        }

        mock_price = {
            "cheapest_retailer": {
                "name": "CheapShop",
                "price": "£80",
                "delivery": "Free",
                "total_price": "£80",
                "total_numeric": 80.0,
            },
            "alternatives": [],
            "savings_vs_original": "£20 cheaper",
            "notes": "",
        }

        MockExtractor.return_value.extract.return_value = mock_product
        MockPricer.return_value.find_best_price.return_value = mock_price
        MockPromo.return_value.find_promos.return_value = None

        orchestrator = OrchestratorAgent()
        asyncio.run(orchestrator.run("https://example.com/product"))

        MockExtractor.return_value.extract.assert_called_once_with(
            "https://example.com/product"
        )
        MockPricer.return_value.find_best_price.assert_called_once_with(mock_product)
        MockPromo.return_value.find_promos.assert_called_once_with(
            mock_product, mock_price
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
