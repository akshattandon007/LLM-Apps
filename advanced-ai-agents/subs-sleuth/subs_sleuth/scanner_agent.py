"""Scanner Agent — finds subscriptions in the user's email."""

from __future__ import annotations

import json
import re
from typing import Optional

from .models import ScanReport, Subscription
from .utils import (
    _LLM_API_KEY,
    connect_imap,
    llm_complete,
    search_subscription_emails,
    web_search,
)


def scan_email(
    server: str = "imap.gmail.com",
    email: str | None = None,
    password: str | None = None,
    search_since: str | None = None,
    limit: int = 200,
) -> ScanReport:
    """Connect to email, search for subscription receipts, extract subscriptions.

    Args:
        server: IMAP server hostname.
        email: Email address for IMAP login.
        password: App password for IMAP login.
        search_since: Date string (e.g. '01-Jan-2025') to search from.
        limit: Max subscription entries to return.

    Returns:
        ScanReport with found subscriptions.
    """
    report = ScanReport()

    if not email or not password:
        report.errors.append("No email credentials provided — use scan_demo() for a demo run.")
        return report

    conn = connect_imap(server, email, password)
    if not conn:
        report.errors.append("Failed to connect to IMAP server.")
        return report

    try:
        email_results = search_subscription_emails(conn, search_since, limit)
        report.email_count_checked = len(email_results)

        for entry in email_results:
            sub = _extract_subscription(entry)
            if sub and sub.merchant:
                report.subscriptions.append(sub)

        report.total_found = len(report.subscriptions)
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    return report


def scan_demo() -> ScanReport:
    """Generate a realistic demo scan with simulated data — no credentials needed."""
    import datetime

    demo_subs = [
        Subscription(
            merchant="Netflix",
            amount=15.99,
            currency="USD",
            billing_url="https://www.netflix.com/account",
            frequency="monthly",
            last_charge_date=(datetime.date.today() - datetime.timedelta(days=5)).isoformat(),
            source_email_subject="Your Netflix receipt",
            source="email",
        ),
        Subscription(
            merchant="Spotify Premium",
            amount=11.99,
            currency="USD",
            billing_url="https://www.spotify.com/account/subscription/",
            frequency="monthly",
            last_charge_date=(datetime.date.today() - datetime.timedelta(days=12)).isoformat(),
            source_email_subject="Your Spotify Premium payment",
            source="email",
        ),
        Subscription(
            merchant="Amazon Prime",
            amount=139.00,
            currency="USD",
            billing_url="https://www.amazon.com/gp/help/customer/ account-info/manage-prime",
            frequency="yearly",
            last_charge_date=(datetime.date.today() - datetime.timedelta(days=60)).isoformat(),
            source_email_subject="Your Amazon Prime membership renewal",
            source="email",
        ),
        Subscription(
            merchant="HBO Max",
            amount=9.99,
            currency="USD",
            billing_url="https://www.max.com/subscriptions",
            frequency="monthly",
            last_charge_date=(datetime.date.today() - datetime.timedelta(days=3)).isoformat(),
            source_email_subject="Payment received — Max",
            source="email",
        ),
        Subscription(
            merchant="ChatGPT Plus",
            amount=20.00,
            currency="USD",
            billing_url="https://chat.openai.com/account/billing",
            frequency="monthly",
            last_charge_date=(datetime.date.today() - datetime.timedelta(days=8)).isoformat(),
            source_email_subject="Your OpenAI subscription receipt",
            source="email",
        ),
        Subscription(
            merchant="Gym Membership — FitLife",
            amount=49.99,
            currency="USD",
            billing_url=None,
            frequency="monthly",
            last_charge_date=(datetime.date.today() - datetime.timedelta(days=1)).isoformat(),
            source_email_subject="FitLife monthly payment",
            source="email",
        ),
    ]

    report = ScanReport(
        subscriptions=demo_subs,
        total_found=len(demo_subs),
        email_count_checked=42,
        scan_date=datetime.datetime.now().isoformat(),
    )
    return report


def _extract_subscription(email_entry: dict) -> Subscription | None:
    """Use LLM or fallback heuristics to extract a subscription from an email."""
    text = f"Subject: {email_entry.get('subject', '')}\n"
    text += f"From: {email_entry.get('sender', '')}\n"
    text += f"Body: {email_entry.get('body_snippet', '')}"

    system_prompt = (
        "You extract subscription information from emails. "
        "Return a JSON object with keys: merchant, amount (number or null), "
        "currency, billing_url (or null), frequency (monthly/yearly/weekly), "
        "and source_email_subject. If the email is NOT about a subscription, "
        'return {"merchant": null}.'
    )

    result = llm_complete(system_prompt, text)

    try:
        data = json.loads(result)
        if not data.get("merchant"):
            # Heuristic fallback
            return _heuristic_extract(email_entry)
        return Subscription(
            merchant=data.get("merchant", "").strip(),
            amount=data.get("amount"),
            currency=data.get("currency", "USD"),
            billing_url=data.get("billing_url"),
            frequency=data.get("frequency", "monthly"),
            source_email_subject=email_entry.get("subject", ""),
        )
    except (json.JSONDecodeError, TypeError):
        return _heuristic_extract(email_entry)


def _heuristic_extract(email_entry: dict) -> Subscription | None:
    """Rule-based extraction when LLM is unavailable."""
    subject = email_entry.get("subject", "")
    known_merchants = {
        "netflix": ("Netflix", "https://www.netflix.com/account"),
        "spotify": ("Spotify Premium", "https://www.spotify.com/account/subscription/"),
        "amazon": ("Amazon Prime", "https://www.amazon.com/gp/help/customer/account-info/manage-prime"),
        "hbo": ("HBO Max", "https://www.max.com/subscriptions"),
        "max": ("HBO Max", "https://www.max.com/subscriptions"),
        "disney": ("Disney+", "https://www.disneyplus.com/account/subscription"),
        "chatgpt": ("ChatGPT Plus", "https://chat.openai.com/account/billing"),
        "openai": ("ChatGPT Plus", "https://chat.openai.com/account/billing"),
        "youtube premium": ("YouTube Premium", "https://www.youtube.com/premium"),
        "apple music": ("Apple Music", "https://music.apple.com/subscription"),
        "hulu": ("Hulu", "https://www.hulu.com/account"),
        "peacock": ("Peacock", "https://www.peacocktv.com/account"),
        "paramount": ("Paramount+", "https://www.paramountplus.com/account"),
    }
    subj_lower = subject.lower()
    # Known merchants require billing keywords too, not just brand name
    billing_keywords = ["receipt", "invoice", "payment", "charge", "billing",
                        "subscription", "renewal", "membership", "premium",
                        "plan", "auto", "monthly", "yearly"]
    has_billing_signal = any(kw in subj_lower for kw in billing_keywords)

    for keyword, (merchant, url) in known_merchants.items():
        if keyword in subj_lower and has_billing_signal:
            return Subscription(
                merchant=merchant,
                billing_url=url,
                source_email_subject=subject,
            )

    # Generic: look for billing/receipt keywords
    if any(kw in subj_lower for kw in ["receipt", "invoice", "payment", "charge", "billing"]):
        # Try several extraction patterns for the service name
        # Pattern: "Your <anything> Receipt — <Service>"
        for sep in [" — ", " —", "—", " – ", " — ", "- "]:
            if sep in subject:
                parts = subject.split(sep)
                merchant = parts[-1].strip()
                # Only take the last part if it looks like a service name (< 80 chars no spaces)
                if merchant and len(merchant) < 80 and merchant[0].isupper():
                    return Subscription(merchant=merchant, source_email_subject=subject)

        # Pattern: "Your <service> receipt/invoice"
        m = re.match(r"Your (.+?) (?:receipt|payment|invoice)", subject, re.IGNORECASE)
        if m:
            merchant = m.group(1).strip()
            return Subscription(merchant=merchant, source_email_subject=subject)

        # Fallback: first 30 chars of subject
        return Subscription(merchant=subject[:30], source_email_subject=subject)

    return None