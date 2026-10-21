"""Tests for the MCP server module."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from docfinder.server import TOOL_DEFINITIONS, TOOL_HANDLERS, _handle_list_tools, _handle_call_tool
from docfinder.nppes_client import Provider
from mcp.types import ListToolsRequest, CallToolRequest, CallToolRequestParams
from mcp.types import Tool as ToolType


def test_tool_definitions():
    """Server exposes the expected tools."""
    tool_names = [t.name for t in TOOL_DEFINITIONS]
    assert "find_providers" in tool_names
    assert "find_by_name" in tool_names
    assert "find_by_zip" in tool_names
    assert "get_provider_details" in tool_names
    assert "find_by_specialty" in tool_names
    assert len(TOOL_DEFINITIONS) >= 5


def test_tool_handlers():
    """Every tool has a handler."""
    for tool in TOOL_DEFINITIONS:
        assert tool.name in TOOL_HANDLERS, f"Missing handler for {tool.name}"
        assert callable(TOOL_HANDLERS[tool.name])


@pytest.mark.asyncio
async def test_handle_list_tools():
    """List tools returns the tool definitions."""
    req = ListToolsRequest(method="tools/list")
    result = await _handle_list_tools(req)
    assert len(result.tools) == len(TOOL_DEFINITIONS)
    assert result.tools[0].name == TOOL_DEFINITIONS[0].name


@pytest.mark.asyncio
async def test_handle_call_tool_unknown():
    """Unknown tool returns error."""
    req = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name="nonexistent", arguments={}),
    )
    result = await _handle_call_tool(req)
    assert result.is_error is True
    assert "Unknown tool" in result.content[0].text


@pytest.mark.asyncio
async def test_handle_call_find_providers():
    """find_providers handler works."""
    from docfinder.server import handle_find_providers
    with patch("docfinder.server._get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.search_providers.return_value = ([], 0)
        mock_get.return_value = mock_client
        
        result = await handle_find_providers({"specialty": "dentist", "city": "Chicago", "state": "IL", "limit": 5})
        assert result.is_error is None or result.is_error is False
        assert "No providers found" in result.content[0].text