"""WhatToWatch — MCP server that tells you what's on TV and what to stream."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from src.models import Show
from src.schedule import daily_schedule, whats_on_right_now, whats_on_tonight
from src.search import search_by_genre, search_show
from src.recommendations import find_similar_shows
from src.tvmaze import TVMazeClient

# Load .env from project root
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

log = logging.getLogger("what-to-watch")
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

app = Server("what-to-watch")


def get_client() -> TVMazeClient:
    """Factory to create a client per request."""
    return TVMazeClient()


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="whats_on_right_now",
            description="What's airing on TV in the current time slot for a given country. "
            "Returns shows with network, rating, genres, and summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "ISO 3166-1 alpha-2 country code (US, GB, CA, AU, etc.)",
                        "default": "US",
                    },
                    "genre": {
                        "type": "string",
                        "description": "Optional genre filter: comedy, drama, cooking, reality, sport, news, documentary, sci-fi, thriller, crime, animation, action",
                    },
                },
            },
        ),
        types.Tool(
            name="whats_on_tonight",
            description="Primetime TV schedule (7PM-11PM) for a given country, optional genre filter. "
            "Returns a curated list of the best shows airing tonight.",
            inputSchema={
                "type": "object",
                "properties": {
                    "genre": {
                        "type": "string",
                        "description": "Optional genre filter: comedy, drama, cooking, reality, sport, news, documentary, sci-fi, thriller, crime, animation, action",
                    },
                    "country": {
                        "type": "string",
                        "description": "ISO 3166-1 alpha-2 country code (US, GB, CA, AU, etc.)",
                        "default": "US",
                    },
                },
            },
        ),
        types.Tool(
            name="search_show",
            description="Search for TV shows by name. Returns network, status, rating, genres, and summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Show name to search for (e.g., 'Breaking Bad', 'Friends')",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="find_similar_shows",
            description="Find shows similar to one you love. Uses genre overlap and rating proximity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_name": {
                        "type": "string",
                        "description": "Name of a show you like (e.g., 'The Office', 'Game of Thrones')",
                    },
                },
                "required": ["show_name"],
            },
        ),
        types.Tool(
            name="daily_schedule",
            description="Full day's TV lineup for any date and country. Returns all scheduled shows.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (defaults to today)",
                    },
                    "country": {
                        "type": "string",
                        "description": "ISO 3166-1 alpha-2 country code (US, GB, CA, AU, etc.)",
                        "default": "US",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(
    name: str,
    arguments: dict,
) -> list[types.TextContent]:
    client = get_client()
    try:
        if name == "whats_on_right_now":
            result = whats_on_right_now(
                client,
                country=arguments.get("country", "US"),
                genre=arguments.get("genre"),
            )
        elif name == "whats_on_tonight":
            result = whats_on_tonight(
                client,
                genre=arguments.get("genre"),
                country=arguments.get("country", "US"),
            )
        elif name == "search_show":
            result = search_show(client, query=arguments["query"])
        elif name == "find_similar_shows":
            result = find_similar_shows(client, show_name=arguments["show_name"])
        elif name == "daily_schedule":
            result = daily_schedule(
                client,
                date=arguments.get("date"),
                country=arguments.get("country", "US"),
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
    finally:
        client.close()

    return [types.TextContent(type="text", text=result)]


async def main() -> None:
    """Run the MCP server over stdio."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="what-to-watch",
                server_version="0.1.0",
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())