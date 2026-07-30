"""The reasoning core: Claude Opus 4.7 with tool-use.

Exposes MCP read tools directly, plus three custom tools the agent uses
to stay inside the rails:

    queue_message_for_approval  — the ONLY way to produce an outbound message
    schedule_cadence            — register a recurring job (with owner OK first)
    set_rota                    — define a named ROTA of Slack users

Every model turn is a loop:
    user msg -> Claude -> (tool calls) -> tool results -> Claude -> ... -> final text

We cap the loop at N iterations to avoid runaway costs.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from anthropic import Anthropic

from .approval_queue import ApprovalQueue
from .config import SYSTEM_PROMPT, Settings
from .scheduler import Scheduler
from .slack_mcp_client import SlackMCPClient


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom (non-MCP) tool schemas exposed to Claude
# ---------------------------------------------------------------------------

CUSTOM_TOOLS: list[dict[str, Any]] = [
    {
        "name": "queue_message_for_approval",
        "description": (
            "Queue an outbound Slack message for the principal's approval. "
            "This is the ONLY way to send messages. The human will receive a "
            "preview 15 minutes before scheduled_send_at (UTC ISO8601). If you "
            "want to send roughly now, set scheduled_send_at to ~16 minutes in "
            "the future."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Slack channel ID (C…) or DM channel (D…) or user ID (U…) for DM.",
                },
                "draft_text": {"type": "string", "description": "Message body."},
                "scheduled_send_at": {
                    "type": "string",
                    "description": "UTC ISO8601 timestamp of intended send.",
                },
                "reason": {
                    "type": "string",
                    "description": "Short explanation of why this message needs to go out.",
                },
                "thread_ts": {
                    "type": "string",
                    "description": "Optional parent message ts to reply in-thread.",
                },
            },
            "required": ["channel", "draft_text", "scheduled_send_at", "reason"],
        },
    },
    {
        "name": "schedule_cadence",
        "description": (
            "Register a recurring job. Use for daily digests, weekly reminders, etc. "
            "Ask the principal to confirm before calling this."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "kind": {"type": "string", "enum": ["cron", "interval"]},
                "spec": {
                    "type": "object",
                    "description": (
                        "For cron: {day_of_week, hour, minute, ...}. "
                        "For interval: {hours: N} or {minutes: N}."
                    ),
                },
                "action": {
                    "type": "string",
                    "enum": ["daily_digest", "rota_reminder", "stale_dm_scan", "custom_draft"],
                },
                "payload": {
                    "type": "object",
                    "description": "Args for the action (e.g. {rota_name, channel, template}).",
                },
            },
            "required": ["name", "kind", "spec", "action"],
        },
    },
    {
        "name": "set_rota",
        "description": "Create or update a named ROTA of Slack user IDs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "members": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ordered list of Slack user IDs (U…).",
                },
                "channel": {
                    "type": "string",
                    "description": "Channel where the rota reminder should be posted.",
                },
            },
            "required": ["name", "members", "channel"],
        },
    },
]


class PMAgent:
    def __init__(
        self,
        settings: Settings,
        mcp: SlackMCPClient,
        approvals: ApprovalQueue,
        scheduler: Scheduler,
        store,
    ):
        self.settings = settings
        self.mcp = mcp
        self.approvals = approvals
        self.scheduler = scheduler
        self.store = store
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self._history: list[dict[str, Any]] = []  # conversation memory
        self._max_history_turns = 20

    # ---------------------------------------------------------- tool registry
    def _tool_definitions(self) -> list[dict[str, Any]]:
        """Read-only MCP tools + our custom approval-gated tools."""
        return self.mcp.read_tools + CUSTOM_TOOLS

    # ---------------------------------------------------------- tool dispatch
    async def _dispatch_tool(self, name: str, args: dict[str, Any]) -> str:
        if name == "queue_message_for_approval":
            try:
                send_at = datetime.fromisoformat(args["scheduled_send_at"].replace("Z", "+00:00"))
            except Exception:
                return "ERROR: scheduled_send_at must be valid ISO8601."
            approval_id = self.approvals.enqueue(
                channel=args["channel"],
                draft_text=args["draft_text"],
                scheduled_send=send_at,
                reason=args.get("reason"),
                thread_ts=args.get("thread_ts"),
            )
            # Wire up the timers
            row = self.store.get_approval(approval_id)
            self.scheduler.schedule_approval_jobs(approval_id, row["scheduled_send"])
            return (
                f"Queued approval #{approval_id}. Principal will be DM'd "
                f"15 min before send ({row['scheduled_send']})."
            )

        if name == "schedule_cadence":
            self.scheduler.register_cadence(
                name=args["name"],
                kind=args["kind"],
                spec=args["spec"],
                action=args["action"],
                payload=args.get("payload") or {},
            )
            return f"Cadence `{args['name']}` registered."

        if name == "set_rota":
            self.store.set_rota(
                name=args["name"],
                members=args["members"],
                channel=args["channel"],
            )
            return f"Rota `{args['name']}` set with {len(args['members'])} members."

        # Otherwise it's an MCP tool — route via the write guard.
        return await self.mcp.safe_call_from_model(name, args)

    # ---------------------------------------------------------- main loop
    async def chat(self, user_message: str, *, max_iterations: int = 8) -> str:
        """One user-turn. Returns the model's final text reply."""
        self._history.append({"role": "user", "content": user_message})
        # Inject current time context — the model can't know it otherwise.
        now_note = {
            "role": "user",
            "content": f"(context: now is {datetime.now(timezone.utc).isoformat()} UTC; "
                       f"principal timezone is {self.settings.timezone})",
        }
        # Trim history to keep context manageable
        trimmed = self._history[-(self._max_history_turns * 2):]
        messages = [now_note] + trimmed

        tools = self._tool_definitions()

        for _ in range(max_iterations):
            resp = self.client.messages.create(
                model=self.settings.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )

            # Collect tool uses and any pre-tool text
            tool_uses = [b for b in resp.content if b.type == "tool_use"]
            if not tool_uses:
                # Terminal response
                text = "".join(b.text for b in resp.content if b.type == "text")
                self._history.append({"role": "assistant", "content": text})
                return text.strip() or "(no reply)"

            # Echo the assistant turn back into the message list
            messages.append({"role": "assistant", "content": resp.content})

            # Run each tool call
            tool_results = []
            for tu in tool_uses:
                log.info("Tool call: %s(%s)", tu.name, json.dumps(tu.input)[:200])
                result = await self._dispatch_tool(tu.name, tu.input or {})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result,
                })
            messages.append({"role": "user", "content": tool_results})

        return "Reached max tool iterations without a final answer. IDK what to do next."
