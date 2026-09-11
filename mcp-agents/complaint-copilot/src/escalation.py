"""Escalation module — generates formal referral letters to regulators/ombudsmen."""

from __future__ import annotations

from datetime import datetime, timezone

from src.models import IssueType, OmbudsmanInfo
from src.ombudsman import find_ombudsman


def _lookup_ombudsman_info(ombudsman: str, company: str) -> OmbudsmanInfo | None:
    """Try to find OmbudsmanInfo matching the given name across all issue types."""
    for issue_type in IssueType:
        results = find_ombudsman(company, issue_type)
        for info in results:
            if ombudsman.lower() in info.name.lower():
                return info
    return None


def escalate_to_regulator(
    company: str,
    ombudsman: str,
    case_summary: str,
    ombudsman_info: OmbudsmanInfo | None = None,
) -> str:
    """Generate a formal referral letter to a regulator or ombudsman.

    Args:
        company: The company being complained about.
        ombudsman: The name of the ombudsman/regulator.
        case_summary: Summary of the case and why escalation is needed.
        ombudsman_info: Optional OmbudsmanInfo object for reference details.

    Returns:
        Formatted referral letter as a string.
    """
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    # Auto-lookup ombudsman info if not provided
    if ombudsman_info is None:
        ombudsman_info = _lookup_ombudsman_info(ombudsman, company)

    url_line = ""
    if ombudsman_info and ombudsman_info.url:
        url_line = f"\nRegulator website: {ombudsman_info.url}"

    return f"""\
REFERRAL TO REGULATORY BODY
DATE: {today}

TO:
{ombudsman}
Office of Consumer Complaints{url_line}

RE: Formal Referral — Complaint Against {company}

Dear Sir or Madam,

I am writing to formally refer a complaint against {company} for your
investigation and intervention. The company has failed to adequately
resolve the matter despite being given a reasonable opportunity to do so.

CASE SUMMARY

{case_summary}

GROUNDS FOR REFERRAL

1. The company was notified of the issue on or before the date of the
   original complaint.
2. The company has failed to provide a satisfactory resolution within a
   reasonable timeframe.
3. The matter falls within your jurisdiction as the appropriate regulatory
   body for this type of complaint.

RELIEF SOUGHT

I respectfully request that your office:

  a) Investigate the conduct of {company} in relation to this matter;
  b) Facilitate a fair resolution between the parties; and
  c) Take any enforcement or remedial action that you consider appropriate
     under your powers and statutory remit.

Please find attached copies of all relevant correspondence, including the
original complaint and any responses received from the company.

I look forward to your acknowledgment of this referral and confirmation
that it has been accepted for investigation.

Yours faithfully,

[Your Name]
[Your Address]
[Your Email]
[Your Phone Number]

---
Referred via Complaint Copilot
"""
