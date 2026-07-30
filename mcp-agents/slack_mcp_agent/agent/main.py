"""Main orchestrator.

Responsibilities:
1. Boot MCP client, store, approval queue, scheduler, agent.
2. Listen for principal commands:
     - Slack DMs (via MCP polling or Socket Mode — simplified here to
       a polling loop; a production build would use Slack Events API)
     - CLI stdin (so the owner can talk to the agent from a terminal too)
3. Parse approval shortcuts: `ok 42`, `cancel 42`, `edit 42 new text`.
4. Anything else → send to Claude for reasoning.
"""
from __future__ import annotations

import asyncio
import logging
import re
import sys
from datetime import datetime, timezone

# Auto-load .env from the repo root so users don't need shell gymnastics.
# Safe no-op if python-dotenv isn't installed or .env doesn't exist.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .actions import Actions
from .agent import PMAgent
from .approval_queue import ApprovalQueue
from .config import Settings
from .memory import Store
from .scheduler import Scheduler
from .slack_mcp_client import SlackMCPClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("main")


APPROVAL_CMD = re.compile(r"^\s*(ok|cancel|edit)\s+(\d+)(?:\s+(.+))?\s*$",
                          re.IGNORECASE | re.DOTALL)


async def run() -> None:
    settings = Settings.from_env()
    store = Store(settings.db_path)

    # Build MCP env (pass Slack tokens down to the server).
    # We inherit the parent PATH so the MCP server's `npx` is findable — without
    # this, stdio_client starts with a near-empty env and "npx" fails with ENOENT.
    import os
    mcp_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "SLACK_BOT_TOKEN": settings.slack_bot_token,
    }
    if settings.slack_user_token:
        mcp_env["SLACK_USER_TOKEN"] = settings.slack_user_token
    if settings.slack_team_id:
        mcp_env["SLACK_TEAM_ID"] = settings.slack_team_id

    async with SlackMCPClient(settings.slack_mcp_server_cmd, env=mcp_env) as mcp:

        # --- DM-to-owner helper: used by approvals + cadences ---------------
        async def dm_owner(text: str) -> None:
            """Send a direct message to the principal. Uses the MCP write
            tool — permitted here because it's internal system-to-owner
            communication (not an outbound message to a stakeholder)."""
            # Find a Slack post tool
            post_tool = next(
                (t["name"] for t in mcp.all_tools if "post" in t["name"].lower()),
                None,
            )
            if not post_tool:
                log.warning("No post tool available; cannot DM owner.")
                print(f"\n[to owner] {text}\n")  # fallback for local dev
                return
            try:
                await mcp.call(post_tool, {
                    "channel": settings.owner_slack_id,
                    "text": text,
                })
            except Exception as e:
                log.exception("Failed to DM owner: %s", e)

        async def send_to_slack(channel: str, text: str, thread_ts: str | None) -> None:
            post_tool = next(
                (t["name"] for t in mcp.all_tools if "post" in t["name"].lower()),
                None,
            )
            if not post_tool:
                raise RuntimeError("No Slack post tool available")
            args = {"channel": channel, "text": text}
            if thread_ts:
                args["thread_ts"] = thread_ts
            await mcp.call(post_tool, args)

        # --- Approval queue + scheduler -------------------------------------
        approvals = ApprovalQueue(
            store=store,
            lead_minutes=settings.approval_lead_minutes,
            owner_slack_id=settings.owner_slack_id,
            notify_owner=dm_owner,
            slack_send=send_to_slack,
        )

        # Agent needs to exist before Actions (Actions calls back into it
        # for summarisation), so we build with a late-binding summariser.
        pending_agent: dict[str, PMAgent] = {}

        async def summarise(prompt: str) -> str:
            return await pending_agent["agent"].chat(prompt)

        actions = Actions(
            store=store, mcp=mcp, approvals=approvals,
            owner_slack_id=settings.owner_slack_id,
            notify_owner=dm_owner, summariser=summarise,
        )

        scheduler = Scheduler(
            store=store,
            approvals=approvals,
            timezone_name=settings.timezone,
            actions=actions.as_map(),
        )

        # Actions need a hook to schedule approval timers when they enqueue
        actions._schedule_timers = lambda aid: scheduler.schedule_approval_jobs(
            aid, store.get_approval(aid)["scheduled_send"]
        )

        agent = PMAgent(
            settings=settings, mcp=mcp, approvals=approvals,
            scheduler=scheduler, store=store,
        )
        pending_agent["agent"] = agent

        scheduler.start()
        log.info("Agent ready. Type to chat; Ctrl-C to exit.")
        log.info("Pending approvals: %d", len(store.list_pending_approvals()))

        # --- Principal command loop (CLI) -----------------------------------
        await _cli_loop(agent, approvals)

        scheduler.shutdown()


async def _cli_loop(agent: PMAgent, approvals: ApprovalQueue) -> None:
    loop = asyncio.get_running_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
        except (KeyboardInterrupt, EOFError):
            break
        if not line:
            await asyncio.sleep(0.1)
            continue
        text = line.rstrip("\n")
        if not text.strip():
            continue

        # Approval shortcuts bypass the LLM
        m = APPROVAL_CMD.match(text)
        if m:
            verb, aid_str, rest = m.group(1).lower(), m.group(2), m.group(3)
            aid = int(aid_str)
            if verb == "ok":
                print(approvals.approve(aid))
            elif verb == "cancel":
                print(approvals.cancel(aid))
            elif verb == "edit":
                if not rest:
                    print("edit requires new text")
                else:
                    print(approvals.edit(aid, rest))
            continue

        # Otherwise: talk to Claude
        try:
            reply = await agent.chat(text)
            print(f"\n{reply}\n")
        except Exception as e:
            log.exception("chat error")
            print(f"[error] {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
