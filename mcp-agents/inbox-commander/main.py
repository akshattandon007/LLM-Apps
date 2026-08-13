#!/usr/bin/env python3
"""Inbox Commander - Gmail MCP server.

Run in MCP stdio mode (default):
    python main.py

Or serve over HTTP (FastAPI + Streamable HTTP):
    python main.py --http --port 8000
"""

from __future__ import annotations

import argparse
import sys

from mcp.server.mcpserver import MCPServer

from src.tools import register

SERVER_NAME = "inbox-commander"


def build_server() -> MCPServer:
    mcp = MCPServer(
        SERVER_NAME,
        instructions=(
            "Inbox Commander: Gmail triage to inbox zero. Search, read, summarize, "
            "draft replies in the user's voice, and label/archive threads. "
            "SENDING IS GATED: to send, first call approve_send with the exact "
            "thread_id and body, then pass the returned approval_token to send_draft. "
            "Never send an email without explicit user approval."
        ),
    )
    register(mcp)
    return mcp


def build_http_app():
    """Optional FastAPI app: health check + MCP tools over Streamable HTTP."""
    from fastapi import FastAPI

    app = FastAPI(title="Inbox Commander MCP", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": SERVER_NAME}

    try:
        app.mount("/mcp", build_server().streamable_http_app())
    except Exception as exc:  # older mcp SDK versions lack the mount helper
        print(f"warning: could not mount MCP HTTP endpoint: {exc}", file=sys.stderr)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Inbox Commander Gmail MCP server")
    parser.add_argument(
        "--http", action="store_true", help="Serve over HTTP (FastAPI) instead of stdio"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.http:
        import uvicorn

        uvicorn.run(build_http_app(), host=args.host, port=args.port)
    else:
        build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
