#!/usr/bin/env python3
"""Verify the MCP server starts and tools are registered."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import mcp

tools = mcp._tool_manager.list_tools()
print(f"Server OK — {len(tools)} tools registered:")
for t in tools:
    print(f"  - {t.name}")
