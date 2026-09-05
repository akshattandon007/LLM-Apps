"""Quick server import check."""
import sys
sys.path.insert(0, "/data/LLM-Apps/mcp-agents/homefix")
from server import server
print(f"MCP Server OK: {server.name}")
tools = server._tool_manager._tools
print(f"Tools registered: {list(tools.keys())}")