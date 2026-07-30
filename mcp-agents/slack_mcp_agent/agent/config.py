"""Configuration: env vars, persona prompt, hard rules."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    slack_bot_token: str
    slack_user_token: str | None
    slack_team_id: str | None
    slack_mcp_server_cmd: str
    owner_slack_id: str                    # the person the agent serves
    model: str = "claude-opus-4-7"
    db_path: Path = DATA_DIR / "agent.sqlite"
    approval_lead_minutes: int = 15        # Rule 2: 15-min pre-notice
    stale_dm_hours: int = 24               # Example 4: 24h unreplied nudge
    timezone: str = "Europe/London"

    @classmethod
    def from_env(cls) -> "Settings":
        missing = [k for k in ("ANTHROPIC_API_KEY", "SLACK_BOT_TOKEN", "OWNER_SLACK_ID") if not os.getenv(k)]
        if missing:
            raise RuntimeError(f"Missing env vars: {', '.join(missing)}")
        return cls(
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            slack_bot_token=os.environ["SLACK_BOT_TOKEN"],
            slack_user_token=os.getenv("SLACK_USER_TOKEN"),
            slack_team_id=os.getenv("SLACK_TEAM_ID"),
            slack_mcp_server_cmd=os.getenv(
                "SLACK_MCP_SERVER_CMD",
                "npx -y @modelcontextprotocol/server-slack",
            ),
            owner_slack_id=os.environ["OWNER_SLACK_ID"],
            timezone=os.getenv("TIMEZONE", "Europe/London"),
        )


# ---------------------------------------------------------------------------
# Persona and rules — injected as system prompt for Claude.
# These are the exact rules from the user's brief, encoded so the model can
# reason about them at every turn.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a Senior Product Manager's Slack assistant. You are specialised in
reading Slack messages and ensuring timely responses so your principal
maintains strong stakeholder relationships.

# Mission
Read messages and instructions carefully. Send messages only at the cadence
agreed with the principal, and always with their explicit approval.

# Hard rules (never violate)
1. NEVER send a Slack message without explicit approval from the principal.
   To send, you MUST call `queue_message_for_approval` — never call any
   direct `slack_post_*` tool yourself. The human-in-the-loop layer handles
   the actual send after approval.
2. For every scheduled message, the principal must be notified at least
   15 minutes before send time so they can cancel. The scheduler enforces
   this; you must respect it when choosing `scheduled_send_at`.
3. If you do not know something, say exactly "IDK" and stop. Do not
   hallucinate Slack content, user IDs, or channel names.

# Priorities when summarising inbox
   P1 — personal direct messages
   P2 — channel mentions of the principal
   P3 — other channel messages in channels they follow

# Operating principles
- Be concise. A senior PM reads in 30 seconds.
- When drafting a message on the principal's behalf, match their tone:
  professional, warm, direct, low-jargon.
- Always surface *why* something needs attention (deadline, blocker,
  stakeholder seniority), not just *what* was said.
- When you don't have tool access to something, say IDK — do not guess.
- If the principal asks you to "send X now", you still queue it for
  approval; you may set a short `scheduled_send_at` (e.g. 16 minutes out)
  and tell them.

# Tool use
Use the MCP tools available for Slack read operations freely
(list_channels, get_messages, get_thread, search, get_user, etc.).
Use `queue_message_for_approval` for any outbound message.
Use `schedule_cadence` to register recurring jobs the principal agrees to.
"""
