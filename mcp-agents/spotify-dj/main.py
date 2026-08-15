"""Spotify DJ — MCP server entry point.

Supports two transport modes:
  - stdio:  `python main.py stdio` (for CLI / Hermes integration)
  - http:   `python main.py http` (Starts uvicorn on port 8000)

Environment variables (from .env):
  SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET — Spotify API credentials
  ANTHROPIC_API_KEY — optional, for Claude-based NL interpretation
"""

from __future__ import annotations

import logging
import os
import sys

import dotenv

from src.tools import register_tools, setup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("spotify-dj")

# Load .env from project root
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def build_mcp_server() -> "MCPServer":
    """Build and configure the MCP server with all tools."""
    try:
        from mcp.server.models import InitializationOptions
        from mcp.server.mcpserver import MCPServer
    except ImportError:
        # Fallback for mcp SDK < 1.x — not ideal but lets us provide a clear error
        raise ImportError(
            "mcp >= 1.0.0 required. Install with: pip install 'mcp>=1.0.0'"
        )

    server = MCPServer(name="spotify-dj")

    # Initialize the Spotify client
    setup()
    logger.info("Spotify client initialized from environment")

    # Register all tools on this server
    register_tools(server)

    return server


def run_stdio() -> None:
    """Run the MCP server over stdio transport (CLI / Hermes integration)."""
    server = build_mcp_server()
    logger.info("Starting spotify-dj MCP server (stdio)...")
    server.run(transport="stdio")


def run_http(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the MCP server over HTTP via FastAPI + uvicorn."""
    server = build_mcp_server()
    logger.info("Starting spotify-dj MCP server (HTTP on %s:%d)...", host, port)

    try:
        import uvicorn
        from fastapi import FastAPI
    except ImportError as e:
        raise ImportError(
            "fastapi and uvicorn required for HTTP mode. "
            "Install with: pip install fastapi uvicorn"
        ) from e

    app = FastAPI(title="Spotify DJ — MCP Agent", version="0.1.0")

    # Mount the MCP server's Starlette app
    try:
        mcp_app = server.streamable_http_app()
        app.mount("/", mcp_app)
    except AttributeError:
        # Fall back to direct FastAPI integration if streamable_http_app
        # is not available in this MCP version
        @app.get("/")
        async def root():
            return {"service": "spotify-dj", "status": "running", "transport": "http"}

        @app.get("/tools")
        async def list_tools():
            return {"tools": list(server.tools.keys()) if hasattr(server, "tools") else []}

    uvicorn.run(app, host=host, port=port)


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <stdio|http>")
        print("  stdio  — Run over stdio transport (default)")
        print("  http   — Run over HTTP via FastAPI")
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode == "http":
        port = int(os.environ.get("PORT", "8000"))
        run_http(port=port)
    elif mode == "stdio":
        run_stdio()
    else:
        print(f"Unknown mode: {mode}. Use 'stdio' or 'http'.")
        sys.exit(1)


if __name__ == "__main__":
    main()