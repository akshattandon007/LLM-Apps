"""Verification Agent — cross-references subscriptions against bank/credit-card statements."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Optional

from .models import StatementLine, Subscription, VerificationReport
from .utils import llm_complete


def verify_subscriptions(
    subscriptions: list[Subscription],
    statement_lines: list[StatementLine],
) -> list[VerificationReport]:
    """Cross-reference each subscription against statement charges.

    Matches by merchant name similarity and expected amount. Returns a
    report for each subscription indicating whether a matching charge
    was found on the statement.
    """
    reports: list[VerificationReport] = []

    for sub in subscriptions:
        best_match: VerificationReport | None = None
        best_score = 0.0

        for line in statement_lines:
            score = _match_score(sub, line)
            if score > best_score:
                best_score = score
                found = score >= 0.3  # minimum threshold to be considered "found"
                best_match = VerificationReport(
                    merchant=sub.merchant,
                    expected_amount=sub.amount,
                    found_on_statement=found,
                    statement_amount=line.amount,
                    statement_date=line.date,
                    match_confidence="high" if score >= 0.8 else "medium" if score >= 0.5 else "low",
                    notes=_generate_notes(sub, line, score),
                )

        if best_match is None:
            reports.append(
                VerificationReport(
                    merchant=sub.merchant,
                    expected_amount=sub.amount,
                    found_on_statement=False,
                    match_confidence="low",
                    notes=f"No matching charge found for {sub.merchant} in the provided statement period.",
                )
            )
        else:
            reports.append(best_match)

    return reports


def verify_demo(subscriptions: list[Subscription] | None = None) -> list[VerificationReport]:
    """Run a demo verification with simulated statement data."""
    import datetime
    today = datetime.date.today()

    if subscriptions is None:
        from .scanner_agent import scan_demo
        report = scan_demo()
        subscriptions = report.subscriptions

    demo_statements = [
        StatementLine(
            date=(today - datetime.timedelta(days=5)).isoformat(),
            description="NETFLIX.COM",
            amount=-15.99,
            category="Entertainment",
        ),
        StatementLine(
            date=(today - datetime.timedelta(days=12)).isoformat(),
            description="SPOTIFY PREMIUM",
            amount=-11.99,
            category="Entertainment",
        ),
        StatementLine(
            date=(today - datetime.timedelta(days=60)).isoformat(),
            description="AMAZON PRIME",
            amount=-139.00,
            category="Shopping",
        ),
        StatementLine(
            date=(today - datetime.timedelta(days=3)).isoformat(),
            description="HBO MAX SUBSCRIPTION",
            amount=-9.99,
            category="Entertainment",
        ),
        StatementLine(
            date=(today - datetime.timedelta(days=8)).isoformat(),
            description="OPENAI CHATGPT",
            amount=-20.00,
            category="Technology",
        ),
        StatementLine(
            date=(today - datetime.timedelta(days=1)).isoformat(),
            description="FITLIFE GYM",
            amount=-49.99,
            category="Health",
        ),
        # Extra non-subscription charges for context
        StatementLine(
            date=(today - datetime.timedelta(days=2)).isoformat(),
            description="UBER EATS",
            amount=-32.50,
            category="Food",
        ),
        StatementLine(
            date=(today - datetime.timedelta(days=4)).isoformat(),
            description="SHEETZ GAS STATION",
            amount=-45.00,
            category="Transportation",
        ),
    ]

    return verify_subscriptions(subscriptions, demo_statements)


def parse_statement_csv(csv_text: str) -> list[StatementLine]:
    """Parse a CSV statement into statement lines.

    Expected columns: date, description, amount (and optionally category).
    Tolerates headers with similar names (Date, Transaction Date, etc.)
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    header_map = _normalize_columns(reader.fieldnames or [])

    lines: list[StatementLine] = []
    for row in reader:
        try:
            date = row.get(header_map.get("date", "") or "", "")
            desc = row.get(header_map.get("description", "") or "", "")
            amount_str = row.get(header_map.get("amount", "") or "", "").strip()
            cat = row.get(header_map.get("category", "") or "", "")
            amount = float(amount_str.replace("$", "").replace(",", ""))
            lines.append(StatementLine(date=date, description=desc, amount=abs(amount), category=cat or None))
        except (ValueError, KeyError):
            continue

    return lines


def _normalize_columns(columns: list[str]) -> dict[str, str]:
    """Map common column names to our canonical keys."""
    mapping: dict[str, list[str]] = {
        "date": ["date", "transaction date", "posting date", "trans date"],
        "description": ["description", "merchant", "transaction", "name", "payee", "details"],
        "amount": ["amount", "charges", "debit", "value", "sum"],
        "category": ["category", "type", "transaction type", "class"],
    }

    result = {}
    for col in columns:
        col_lower = col.lower().strip()
        for canonical, alternatives in mapping.items():
            if col_lower in alternatives or col_lower == canonical:
                result[canonical] = col
                break
    return result


def _match_score(sub: Subscription, line: StatementLine) -> float:
    """Score how well a subscription matches a statement line (0.0-1.0)."""
    score = 0.0

    # Merchant name similarity — substring check (e.g. "netflix" in "netflix.com")
    sub_name = sub.merchant.lower()
    desc_name = line.description.lower()
    if sub_name in desc_name or desc_name in sub_name:
        score += 0.5
    else:
        # Token-level overlap for partial matches
        sub_words = set(sub_name.split())
        desc_words = set(desc_name.split())
        common = sub_words & desc_words
        if common:
            score += 0.3 * (len(common) / max(len(sub_words), len(desc_words), 1))

    # Amount match
    if sub.amount is not None and line.amount:
        amount_diff = abs(abs(line.amount) - sub.amount)
        if amount_diff < 0.01:
            score += 0.5
        elif amount_diff < 1.0:
            score += 0.3
        elif amount_diff < 5.0:
            score += 0.1

    # Amount direction (only boosts when name already matches)
    if line.amount < 0 and score > 0:
        score += 0.05

    return min(score, 1.0)


def _generate_notes(sub: Subscription, line: StatementLine, score: float) -> str:
    """Generate human-readable notes about the match."""
    if score >= 0.8:
        return f"Strong match: {line.description} for ${abs(line.amount):.2f} on {line.date}"
    elif score >= 0.5:
        return f"Partial match: {line.description} for ${abs(line.amount):.2f} on {line.date} — verify amount"
    else:
        return f"Weak match: {line.description} but amount/name don't align perfectly"