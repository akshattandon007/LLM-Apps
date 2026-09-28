"""Tests for MediMate OpenFDA client and MCP server."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from medimate.client import OpenFDAClient
from server import _format_result


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_http() -> MagicMock:
    """Return a mock httpx.Client with a canned JSON response."""
    client = MagicMock(spec=httpx.Client)
    client.get.return_value.json.return_value = {
        "meta": {"results": {"total": 1}},
        "results": [
            {
                "openfda": {
                    "brand_name": ["TestBrand"],
                    "generic_name": ["test"],
                    "substance_name": ["TEST SUBSTANCE"],
                    "manufacturer_name": ["TestCo"],
                },
                "warnings": ["Test warning"],
                "drug_interactions": ["Test interaction"],
            }
        ],
    }
    client.get.return_value.raise_for_status = MagicMock()
    return client


@pytest.fixture
def client(mock_http: MagicMock) -> OpenFDAClient:
    return OpenFDAClient(http_client=mock_http)


# ── Client tests ──────────────────────────────────────────────────────

class TestOpenFDAClient:
    def test_search_drug(self, client: OpenFDAClient, mock_http: MagicMock) -> None:
        result = client.search_drug("TestBrand")
        assert result["total"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["_brand_name"] == "TestBrand"
        mock_http.get.assert_called_once()
        url = str(mock_http.get.call_args[0][0])
        assert "/drug/label.json" in url

    def test_search_drug_zero_results(self, mock_http: MagicMock) -> None:
        mock_http.get.return_value.json.return_value = {
            "meta": {"results": {"total": 0}},
            "results": [],
        }
        client = OpenFDAClient(http_client=mock_http)
        result = client.search_drug("NonexistentDrug")
        assert result["total"] == 0
        assert len(result["results"]) == 0

    def test_get_adverse_events(self, client: OpenFDAClient, mock_http: MagicMock) -> None:
        result = client.get_adverse_events("Aspirin")
        assert result["total"] == 1
        # Should hit the event endpoint
        url = str(mock_http.get.call_args[0][0])
        assert "/drug/event.json" in url

    def test_find_generic_brands(self, client: OpenFDAClient, mock_http: MagicMock) -> None:
        result = client.find_generic_brands("acetaminophen")
        assert result["total"] == 1

    def test_browse_ingredients(self, client: OpenFDAClient, mock_http: MagicMock) -> None:
        result = client.browse_ingredients(limit=10, page=2)
        assert result["total"] == 1
        # Check skip parameter for page 2 with limit 10
        called_params = mock_http.get.call_args[1].get("params", {})
        assert called_params.get("skip") == 10

    def test_ndc_lookup(self, client: OpenFDAClient, mock_http: MagicMock) -> None:
        result = client.get_by_ndc("12345-6789-0")
        assert result["total"] == 1
        url = str(mock_http.get.call_args[0][0])
        assert "/drug/ndc.json" in url

    def test_search_ndc(self, client: OpenFDAClient, mock_http: MagicMock) -> None:
        result = client.search_ndc("Tylenol")
        assert result["total"] == 1

    def test_close(self, client: OpenFDAClient, mock_http: MagicMock) -> None:
        client.close()
        mock_http.close.assert_called_once()


# ── Result formatting tests ───────────────────────────────────────────

class TestFormatResult:
    def test_basic_formatting(self) -> None:
        data = {
            "total": 2,
            "results": [
                {
                    "_brand_name": "DrugA",
                    "_generic_name": "genericA",
                    "_active_ingredients": ["subA"],
                    "_manufacturer": "MfrA",
                    "_warnings": "Warning text",
                },
                {
                    "_brand_name": "DrugB",
                    "_generic_name": "genericB",
                    "_active_ingredients": ["subB"],
                    "_manufacturer": "MfrB",
                },
            ],
        }
        text = _format_result(data, "Test Label")
        assert "## Test Label" in text
        assert "2 result(s)" in text
        assert "DrugA" in text
        assert "DrugB" in text
        assert "Warning text" in text
        assert "subA" in text
        assert "subB" in text

    def test_empty_results(self) -> None:
        data = {"total": 0, "results": [], "meta": {}, "pages": 0}
        text = _format_result(data, "Empty")
        assert "0 result(s)" in text
        assert "Empty" in text


# ── Server tool routing tests ─────────────────────────────────────────

class TestServerTools:
    @pytest.mark.asyncio
    async def test_list_tools(self) -> None:
        from server import handle_list_tools
        tools = await handle_list_tools()
        names = [t.name for t in tools]
        assert "search_drug" in names
        assert "check_adverse_events" in names
        assert "find_generic_alternatives" in names
        assert "ndc_lookup" in names
        assert "browse_drugs" in names
        assert len(tools) == 5

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self) -> None:
        from server import handle_call_tool
        result = await handle_call_tool("nonexistent", {})
        assert len(result) == 1
        assert "Unknown tool" in result[0].text


class TestClientIntegration:
    """Simplified tests that check live API responses from OpenFDA."""

    @pytest.mark.slow
    def test_live_search_drug(self) -> None:
        """Search for a real drug and verify response shape."""
        client = OpenFDAClient()
        result = client.search_drug("Tylenol", limit=3)
        assert result["total"] > 0
        assert len(result["results"]) > 0
        r = result["results"][0]
        # At minimum brand_name should be resolved
        assert "_brand_name" in r
        client.close()

    @pytest.mark.slow
    def test_live_adverse_events(self) -> None:
        """Verify the events endpoint returns real data for a common drug."""
        client = OpenFDAClient()
        result = client.get_adverse_events("Aspirin", limit=3)
        assert result["total"] > 0
        client.close()