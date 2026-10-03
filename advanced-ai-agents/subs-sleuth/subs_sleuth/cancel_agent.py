"""Cancellation Agent — researches how to cancel each subscription."""

from __future__ import annotations

from typing import Optional

from .models import CancellationGuide, Subscription
from .utils import llm_complete, web_search


def research_cancellation(sub: Subscription) -> CancellationGuide:
    """Research how to cancel a single subscription.

    Uses web search to find cancellation instructions, then LLM to
    synthesise a step-by-step guide.

    Falls back to a known cancellation database for major services.
    """
    guide = CancellationGuide(merchant=sub.merchant)

    # 1. Check known cancellation database first
    known = _known_cancellation(sub.merchant)
    if known:
        guide = known
        return guide

    # 2. Search the web for cancellation instructions
    query = f"how to cancel {sub.merchant} subscription 2026"
    if sub.billing_url:
        query = f"how to cancel {sub.merchant} subscription {sub.billing_url}"

    results = web_search(query)

    # 3. Use LLM to synthesise cancellation guide from search results
    search_text = "\n".join(
        f"- {r.get('title', '')}: {r.get('url', '')}" for r in results
    )

    system_prompt = (
        "You create step-by-step cancellation guides for subscriptions. "
        "Return a JSON object with:\n"
        '- "method": "website" | "phone" | "email" | "app"\n'
        '- "steps": list of strings, each a clear action step\n'
        '- "url": the cancellation page URL or null\n'
        '- "phone_number": if phone cancellation, the number or null\n'
        '- "notes": any gotchas or tips (e.g. "Must cancel before 24h of next billing")\n'
        '- "difficulty": "easy" | "medium" | "hard"\n'
        "Be specific and accurate. If unsure, return what's commonly true."
    )

    user_prompt = (
        f"Cancellation research for: {sub.merchant}\n"
        f"Billing URL: {sub.billing_url or 'unknown'}\n"
        f"Search results:\n{search_text}"
    )

    result = llm_complete(system_prompt, user_prompt)

    import json
    try:
        data = json.loads(result)
        guide.cancellation_method = data.get("method", "website")
        guide.steps = data.get("steps", [])
        guide.url = data.get("url") or sub.billing_url
        guide.phone_number = data.get("phone_number")
        guide.notes = data.get("notes")
        guide.difficulty = data.get("difficulty", "medium")
    except (json.JSONDecodeError, TypeError):
        # Fallback: use basic info
        guide.steps = [
            f"Go to {sub.billing_url or 'the service website'}",
            "Navigate to Account Settings or Subscription",
            "Look for Cancel Subscription or Cancel Plan",
            "Follow the cancellation flow — may need to confirm via email",
        ]
        guide.url = sub.billing_url

    return guide


def research_all(subscriptions: list[Subscription]) -> list[CancellationGuide]:
    """Research cancellation for all subscriptions."""
    return [research_cancellation(sub) for sub in subscriptions]


def _known_cancellation(merchant: str) -> CancellationGuide | None:
    """Known cancellation paths for major services — no lookups needed."""
    database: dict[str, dict] = {
        "Netflix": {
            "method": "website",
            "steps": [
                "Go to netflix.com and sign in",
                "Click your profile icon → Account",
                "Click 'Cancel Membership' under Plan Details",
                "Confirm cancellation — service continues until billing period ends",
            ],
            "url": "https://www.netflix.com/account",
            "difficulty": "easy",
            "notes": "Netflix saves your profile for 10 months in case you return.",
        },
        "Spotify Premium": {
            "method": "website",
            "steps": [
                "Go to spotify.com/account and sign in",
                "Click 'Your Plan' in the sidebar",
                "Scroll down and click 'CHANGE PLAN'",
                "Scroll to the bottom and click 'Cancel Spotify Premium'",
                "Confirm cancellation — Spotify may offer a discounted rate to stay",
            ],
            "url": "https://www.spotify.com/account/subscription/",
            "difficulty": "easy",
            "notes": "You keep Premium until next billing date. Spotify often offers 3 months at $0.99 to retain you.",
        },
        "Amazon Prime": {
            "method": "website",
            "steps": [
                "Go to amazon.com and sign in",
                "Hover over 'Account & Lists' → 'Your Account'",
                "Under 'Membership & Subscriptions', click 'Manage Prime Membership'",
                "Click 'End Membership' and follow the prompts",
                "Confirm at the next screen",
            ],
            "url": "https://www.amazon.com/gp/help/customer/account-info/manage-prime",
            "difficulty": "medium",
            "notes": "Amazon puts cancellation behind multiple confirmation screens. Some users report needing to click through 3+ prompts.",
        },
        "HBO Max": {
            "method": "website",
            "steps": [
                "Go to max.com and sign in (or open the Max app)",
                "Click your profile icon → 'Subscription'",
                "Click 'Manage Subscription'",
                "Click 'Cancel Subscription'",
                "Select a reason and confirm",
            ],
            "url": "https://www.max.com/subscriptions",
            "difficulty": "easy",
            "notes": "If subscribed through a third party (Apple, Amazon), you must cancel there.",
        },
        "ChatGPT Plus": {
            "method": "website",
            "steps": [
                "Go to chat.openai.com and sign in",
                "Click your profile picture → 'Settings' → 'Billing'",
                "Under 'Plan', click 'Cancel Plan'",
                "Select 'I want to cancel my plan' and confirm",
            ],
            "url": "https://chat.openai.com/account/billing",
            "difficulty": "easy",
            "notes": "Your Plus benefits continue until the next billing date.",
        },
        "Disney+": {
            "method": "website",
            "steps": [
                "Log in to disneyplus.com",
                "Click your profile icon → 'Account'",
                "Click 'Subscription' → 'Cancel Subscription'",
                "Follow the cancellation prompts",
            ],
            "url": "https://www.disneyplus.com/account/subscription",
            "difficulty": "easy",
        },
        "YouTube Premium": {
            "method": "website",
            "steps": [
                "Go to youtube.com and sign in",
                "Click your profile picture → 'Paid memberships'",
                "Next to 'YouTube Premium', click 'Manage'",
                "Click 'Cancel membership' and confirm",
            ],
            "url": "https://www.youtube.com/premium",
            "difficulty": "easy",
            "notes": "If subscribed via Google Play on iOS, you must cancel through Apple's subscription settings.",
        },
        "Hulu": {
            "method": "website",
            "steps": [
                "Log in to hulu.com",
                "Click your profile icon → 'Account'",
                "Under 'Manage Your Subscription', click 'Cancel'",
                "Follow the prompts to confirm",
            ],
            "url": "https://www.hulu.com/account",
            "difficulty": "medium",
            "notes": "Hulu shows a 'Take a Break' pause option before the full cancellation — you want 'Cancel' not 'Pause'.",
        },
        "FitLife": None,  # Not in the database — will use web search
    }

    entry = database.get(merchant)
    if entry is None:
        return None
    return CancellationGuide(
        merchant=merchant,
        cancellation_method=entry["method"],
        steps=entry["steps"],
        url=entry.get("url"),
        phone_number=entry.get("phone_number"),
        notes=entry.get("notes"),
        difficulty=entry.get("difficulty", "medium"),
        source="known_database",
    )