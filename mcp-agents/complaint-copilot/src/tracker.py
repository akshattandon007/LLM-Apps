"""Complaint tracker — in-memory status tracking with escalation history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from src.models import ComplaintStatus

# ---------------------------------------------------------------------------
# In-memory complaint tracking.
#
# v0.1 uses an in-memory dict — ephemeral, resets on server restart. A future
# version could persist to SQLite or a database.
# ---------------------------------------------------------------------------

_store: dict[str, ComplaintStatus] = {}


def create_tracker(company: str, reference: str) -> ComplaintStatus:
    """Create a new tracking entry for a complaint."""
    status = ComplaintStatus(
        reference=reference,
        company=company,
        status="pending",
        notes=["Complaint created."],
        next_action="Awaiting company response. Follow up in 14 days.",
    )
    _store[reference] = status
    return status


def get_status(reference: str) -> Optional[ComplaintStatus]:
    """Get the status of a tracked complaint by reference."""
    return _store.get(reference)


def update_status(
    reference: str,
    status: Optional[str] = None,
    note: Optional[str] = None,
    next_action: Optional[str] = None,
) -> Optional[ComplaintStatus]:
    """Update a complaint's status."""
    entry = _store.get(reference)
    if entry is None:
        return None

    if status:
        entry.status = status
    if note:
        entry.notes.append(note)
    if next_action:
        entry.next_action = next_action
    entry.updated_at = datetime.now(timezone.utc)
    return entry


def track_complaint(company: str, reference: Optional[str] = None) -> str:
    """Get the status template and next action for a complaint.

    If reference is provided and exists, return current status.
    If not, return a template for what to expect.
    """
    if reference and reference in _store:
        entry = _store[reference]
        lines = [
            f"Complaint Reference: {entry.reference}",
            f"Company: {entry.company}",
            f"Status: {entry.status}",
            f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"Last Updated: {entry.updated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "Timeline:",
        ]
        for note in entry.notes:
            lines.append(f"  - {note}")
        lines.append("")
        if entry.next_action:
            lines.append(f"Next action: {entry.next_action}")
        return "\n".join(lines)

    # Return a template with what the user should do
    if reference:
        # Create a new tracker entry
        entry = create_tracker(company, reference)
        return track_complaint(company, reference)

    return f"""\
Complaint Tracking — {company}

No reference number provided. To track a complaint, please provide the
reference number from your complaint letter.

Typical escalation stages:
  1. PENDING    — Complaint sent, awaiting company response
  2. AWAITING_REPLY — Company acknowledged, investigating
  3. RESPONDED  — Company has responded with a decision
  4. ESCALATED  — Escalated to ombudsman/regulator
  5. RESOLVED   — Complaint resolved
  6. CLOSED     — Case closed

Next action: Follow up with the company if no response within 14 days.
"""
