"""
Letter Drafter Agent — Drafts formal insurance claim letters, appeal letters,
and follow-up correspondence based on policy details and claim circumstances.
"""

from typing import Dict, Optional

from utils.llm_utils import LLMClient, get_llm_client


LETTER_SYSTEM = """You are a professional legal correspondence writer specializing in
insurance claims. Write clear, formal, persuasive letters that include:
- All relevant identifying information (policy number, claim number, dates)
- A clear statement of what is being requested
- References to specific policy terms where applicable
- A call to action and deadline for response
- Professional tone, no emotional language

Adapt the letter type based on the request:
- initial_claim: First notice of loss / claim filing
- appeal: Appeal of a denied or underpaid claim
- follow_up: Polite reminder after no response
- request_info: Request for policy documents or claim file
- complaint: Formal complaint about handling

Output ONLY the letter text, ready to print and send. Include [DATE] and [YOUR_NAME]
as placeholders where the user should fill in personal details."""


class LetterDrafterAgent:
    """
    Agent 4: Drafts formal insurance correspondence.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()

    def draft_letter(
        self,
        letter_type: str,
        claim_info: Dict,
        additional_instructions: Optional[str] = None,
    ) -> str:
        """
        Draft an insurance claim letter.

        Args:
            letter_type: initial_claim | appeal | follow_up | request_info | complaint
            claim_info: Dict with keys like policy_number, insurance_company,
                       claim_number, incident_description, etc.
            additional_instructions: Any extra context for the letter.

        Returns:
            Formatted letter text.
        """
        info_lines = "\n".join([f"  {k}: {v}" for k, v in claim_info.items()])
        extra = f"\nAdditional instructions: {additional_instructions}" if additional_instructions else ""

        user_prompt = f"""Write a {letter_type.replace('_', ' ')} letter with these details:

Claim Information:
{info_lines}
{extra}

Write a professional letter ready to send. Use [DATE] and [YOUR_NAME] as placeholders.
Include a specific subject line. Format with sender/date blocks at top."""

        return self.llm.chat(
            system_prompt=LETTER_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.3,
        )

    def draft_initial_claim(
        self,
        policy_number: str,
        insurance_company: str,
        claim_type: str,
        incident_date: str,
        incident_description: str,
        estimated_damages: Optional[str] = None,
    ) -> str:
        """Convenience method to draft a first notice of loss."""
        return self.draft_letter(
            letter_type="initial_claim",
            claim_info={
                "Policy Number": policy_number,
                "Insurance Company": insurance_company,
                "Claim Type": claim_type,
                "Incident Date": incident_date,
                "Incident Description": incident_description,
                "Estimated Damages": estimated_damages or "TBD",
            },
        )

    def draft_appeal(
        self,
        policy_number: str,
        insurance_company: str,
        claim_number: str,
        denial_reason: str,
        policy_basis: str,
        additional_evidence: Optional[str] = None,
    ) -> str:
        """Draft an appeal letter for a denied claim."""
        return self.draft_letter(
            letter_type="appeal",
            claim_info={
                "Policy Number": policy_number,
                "Insurance Company": insurance_company,
                "Claim Number": claim_number,
                "Denial Reason": denial_reason,
                "Policy Basis for Appeal": policy_basis,
                "Additional Evidence": additional_evidence or "See attached",
            },
        )

    def draft_follow_up(self, claim_info: Dict) -> str:
        """Draft a follow-up letter for a claim that's gone unanswered."""
        return self.draft_letter(
            letter_type="follow_up",
            claim_info=claim_info,
        )