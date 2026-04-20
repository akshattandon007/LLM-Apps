"""Slack MCP client.

Wraps the MCP Python SDK to expose Slack tools (list_channels, get_messages,
post_message, etc.) as callable functions. Crucially: any tool whose name
starts with `slack_post_` or `slack_send_` is BLOCKED from direct invocation
by the model — the agent must route through the approval queue. This is
the teeth behind Rule 1.
"""
from __future__ import annotations

import asyncio
import logging
import shlex
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


log = logging.getLogger(__name__)

# Substrings that identify Slack write/mutation tools. Any MCP tool whose
# (lowercased) name contains one of these is blocked from the model loop.
# We cast a wide net — different MCP Slack servers name these differently.
WRITE_TOOL_MARKERS = (
    "post_message", "postmessage",
    "send_message", "sendmessage",
    "post_ephemeral", "update_message", "delete_message",
    "reactions_add", "reactions.add",
    "files_upload", "files.upload",
    "schedule_message", "chat_schedule",
    "conversations_invite", "conversations_archive",
    "pins_add", "stars_add",
)


class SlackMCPClient:
    """Async context-managed MCP client for Slack."""

    def __init__(self, server_cmd: str, env: dict[str, str] | None = None):
        self.server_cmd = server_cmd
        self.env = env or {}
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._tools: list[dict[str, Any]] = []

    async def __aenter__(self) -> "SlackMCPClient":
        self._stack = AsyncExitStack()
        parts = shlex.split(self.server_cmd)
        params = StdioServerParameters(command=parts[0], args=parts[1:], env=self.env)

        read, write = await self._stack.enter_async_context(stdio_client(params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()

        listed = await self._session.list_tools()
        self._tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            for t in listed.tools
        ]
        log.info("Connected to Slack MCP server, %d tools available", len(self._tools))
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._stack:
            await self._stack.aclose()

    # ---------------------------------------------------------------- API
    @property
    def read_tools(self) -> list[dict[str, Any]]:
        """Tools safe for Claude to call directly (read-only)."""
        return [t for t in self._tools if not self._is_write(t["name"])]

    @property
    def all_tools(self) -> list[dict[str, Any]]:
        return self._tools

    @staticmethod
    def _is_write(name: str) -> bool:
        n = name.lower()
        return any(marker in n for marker in WRITE_TOOL_MARKERS)

    async def call(self, name: str, arguments: dict[str, Any]) -> Any:
        """Invoke an MCP tool. Write tools are only callable from trusted
        internal code (approval_queue.send), never from the model loop."""
        if self._session is None:
            raise RuntimeError("Session not initialised")
        result = await self._session.call_tool(name, arguments=arguments)
        # MCP returns a list of content blocks — flatten text blocks
        out: list[str] = []
        for block in result.content:
            if hasattr(block, "text"):
                out.append(block.text)
        return "\n".join(out) if out else str(result.content)

    async def safe_call_from_model(self, name: str, arguments: dict[str, Any]) -> str:
        """Guard: called when the LLM invokes a tool. Blocks write ops."""
        if self._is_write(name):
            return (
                f"BLOCKED: `{name}` is a write operation. You must not call it "
                "directly. Use `queue_message_for_approval` instead so the "
                "principal can review before send."
            )
        try:
            return await self.call(name, arguments)
        except Exception as e:
            log.exception("MCP tool %s failed", name)
            return f"ERROR calling {name}: {e}"
