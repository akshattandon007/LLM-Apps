"""One-time setup: register the four canonical cadences from the brief.

Run this ONCE after first boot. It persists the cadences into SQLite; on
every subsequent start the scheduler will reload them automatically.

Usage:
    # Edit the CONFIG block below with your channel IDs / rota members, then:
    python setup_cadences.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.config import Settings
from agent.memory import Store


# ---------------------------------------------------------------------------
# EDIT THESE before running
# ---------------------------------------------------------------------------

PRE_PULSE_CHANNEL = "C0123456789"   # channel where the weekly reminder posts
PRE_PULSE_ROTA = ["U_ALICE", "U_BOB", "U_CHARLIE", "U_DIYA"]  # Slack user IDs


def main() -> None:
    settings = Settings.from_env()
    store = Store(settings.db_path)

    # 1) Define the ROTA that the Friday reminder will cycle through
    store.set_rota(
        name="pre_pulse",
        members=PRE_PULSE_ROTA,
        channel=PRE_PULSE_CHANNEL,
    )
    print(f"✓ ROTA `pre_pulse` set with {len(PRE_PULSE_ROTA)} members → {PRE_PULSE_CHANNEL}")

    # 2) Daily morning digest — 08:30 local time, weekdays
    store.upsert_cadence(
        name="daily_morning_digest",
        kind="cron",
        spec={"day_of_week": "mon-fri", "hour": 8, "minute": 30},
        action="daily_digest",
        payload={},
    )
    print("✓ Cadence `daily_morning_digest` → weekdays 08:30")

    # 3) Weekly ROTA reminder — Fridays 10:00 local
    store.upsert_cadence(
        name="friday_pre_pulse",
        kind="cron",
        spec={"day_of_week": "fri", "hour": 10, "minute": 0},
        action="rota_reminder",
        payload={
            "rota_name": "pre_pulse",
            "template": (
                "Hey <@{user}> — you're up on the pre-pulse this week. "
                "Please share an update in-thread by EOD today. 🙏"
            ),
        },
    )
    print("✓ Cadence `friday_pre_pulse` → Fridays 10:00 (drafts to approval queue)")

    # 4) Stale DM scan — hourly
    store.upsert_cadence(
        name="stale_dm_scan",
        kind="interval",
        spec={"hours": 1},
        action="stale_dm_scan",
        payload={"hours": settings.stale_dm_hours},
    )
    print(f"✓ Cadence `stale_dm_scan` → hourly (flag DMs unanswered >{settings.stale_dm_hours}h)")

    print("\nAll cadences registered. Start the agent with `python -m agent.main`.")


if __name__ == "__main__":
    main()
