"""
Timeline Tracker Agent — Tracks claim filing deadlines, statutory timelines,
and sends reminders about next steps based on the claim type and state.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config import CLAIM_DEADLINES
from utils.llm_utils import LLMClient, get_llm_client


STATUTE_SYSTEM = """You are a legal timeline specialist for insurance claims.
Given the claim type, state, and incident date, calculate:
1. The filing deadline (statute of limitations)
2. The expected timeline for the insurer to respond (based on state regulations)
3. Key milestones in the claims process
4. What happens if deadlines are missed

Respond as JSON:
{
  "incident_date": "YYYY-MM-DD",
  "filing_deadline": "YYYY-MM-DD",
  "days_remaining": number,
  "insurer_response_deadline_days": "typical N days",
  "key_milestones": [
    {"step": "...", "deadline": "YYYY-MM-DD or 'N days after filing'", "description": "..."}
  ],
  "missed_deadline_consequences": "or null if not applicable",
  "urgent": true/false
}"""


class TimelineTrackerAgent:
    """
    Agent 3: Tracks claim timelines, deadlines, and next-step reminders.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()

    def get_filing_deadline_days(self, state_code: str) -> int:
        """Get the statute of limitations (in days) for a given US state."""
        return CLAIM_DEADLINES.get(state_code.upper(), 365)

    def calculate_timeline(
        self,
        claim_type: str,
        state_code: str,
        incident_date_str: str,
    ) -> Dict:
        """
        Calculate the complete claim timeline.

        Args:
            claim_type: auto, home, health, life, travel
            state_code: Two-letter US state code
            incident_date_str: Date of incident in YYYY-MM-DD format

        Returns:
            Dict with timeline information.
        """
        try:
            incident_date = datetime.strptime(incident_date_str, "%Y-%m-%d")
        except ValueError:
            return {"error": f"Invalid date format: {incident_date_str}. Use YYYY-MM-DD."}

        today = datetime.now()
        deadline_days = self.get_filing_deadline_days(state_code)
        filing_deadline = incident_date + timedelta(days=deadline_days)
        days_remaining = (filing_deadline - today).days
        days_since_incident = (today - incident_date).days

        result = {
            "incident_date": incident_date_str,
            "state": state_code,
            "filing_deadline_days_after_incident": deadline_days,
            "filing_deadline": filing_deadline.strftime("%Y-%m-%d"),
            "days_since_incident": days_since_incident,
            "days_remaining": max(0, days_remaining),
            "is_overdue": days_remaining < 0,
            "status": "OVERDUE" if days_remaining < 0 else "URGENT" if days_remaining < 30 else "OK",
        }

        # Generate milestones
        milestones = []

        # File the claim
        milestones.append({
            "step": "File claim",
            "deadline": filing_deadline.strftime("%Y-%m-%d"),
            "days_from_now": max(0, days_remaining),
            "description": "Submit claim to insurance company",
        })

        # Insurer acknowledgement (typically 5-15 days)
        ack_deadline = today + timedelta(days=15)
        milestones.append({
            "step": "Insurer acknowledgment",
            "deadline": ack_deadline.strftime("%Y-%m-%d"),
            "days_from_now": 15,
            "description": "Insurer should acknowledge receipt within 15 days",
        })

        # Investigation period (typically 30-45 days)
        inv_deadline = today + timedelta(days=45)
        milestones.append({
            "step": "Investigation deadline",
            "deadline": inv_deadline.strftime("%Y-%m-%d"),
            "days_from_now": 45,
            "description": "Insurer has up to 45 days to investigate (varies by state)",
        })

        # Decision deadline
        decision_deadline = today + timedelta(days=60)
        milestones.append({
            "step": "Claim decision",
            "deadline": decision_deadline.strftime("%Y-%m-%d"),
            "days_from_now": 60,
            "description": "Expected claim decision (approve/deny)",
        })

        result["milestones"] = milestones

        # Use LLM enriched analysis if available
        if self.llm.api_key:
            try:
                enriched = self.llm.extract_json(
                    system_prompt=STATUTE_SYSTEM,
                    user_prompt=f"Analyze timeline for {claim_type} claim in {state_code}, incident date {incident_date_str}",
                )
                if "error" not in enriched:
                    result["llm_analysis"] = enriched
            except Exception:
                pass

        return result

    def get_next_steps(self, timeline: Dict) -> List[str]:
        """Generate actionable next steps based on timeline status."""
        steps = []

        if timeline.get("is_overdue"):
            steps.append(
                "⚠️ Your deadline has passed! Contact an insurance attorney immediately. "
                "Some states allow late filings under special circumstances."
            )
            return steps

        remaining = timeline.get("days_remaining", 365)

        if remaining < 7:
            steps.append("🚨 File your claim NOW — less than a week before deadline!")
        elif remaining < 30:
            steps.append(f"⏰ {remaining} days left. Prepare documents and file within 2 weeks.")
        else:
            steps.append(f"✅ You have {remaining} days. Plenty of time — but don't procrastinate.")

        steps.append("📄 Step 1: Gather all required documents (use the Document Collector)")
        steps.append("📋 Step 2: Review your policy for coverage details (use the Policy Parser)")
        steps.append("📝 Step 3: Draft your claim letter (use the Letter Drafter)")
        steps.append("📬 Step 4: Submit claim and track milestones")

        return steps