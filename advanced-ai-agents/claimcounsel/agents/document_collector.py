"""
Document Collector Agent — Inventories and organizes claim-related documents.
Checks what documents are present vs. what's needed for a specific claim type.
"""

from typing import Dict, List, Optional
from config import CLAIM_TYPE_DOCUMENTS
from utils.llm_utils import LLMClient, get_llm_client
from utils.file_utils import read_all_texts, list_claim_files


DOCUMENT_CHECKER_SYSTEM = """You are a claims document specialist. Given a claim type,
a list of available documents, and the filenames, tell the user:
1. Which required documents they have
2. Which required documents are missing
3. Whether each available document actually contains relevant content (check the text)
4. Any additional documents that might strengthen their claim

Respond as a JSON object:
{
  "claim_type": "...",
  "documents_present": [{"name": "...", "has_content": true/false, "notes": "..."}],
  "documents_missing": ["..."],
  "additional_recommendations": ["..."],
  "readiness_score": "LOW | MEDIUM | HIGH"
}"""


class DocumentCollectorAgent:
    """
    Agent 2: Scans the claim folder, identifies what documents exist,
    and compares against the requirements for the claim type.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()

    def get_required_documents(self, claim_type: str) -> List[str]:
        """Get the standard required documents for a claim type."""
        return CLAIM_TYPE_DOCUMENTS.get(claim_type.lower(), CLAIM_TYPE_DOCUMENTS.get("auto", []))

    def inventory_documents(self, documents_dir: str) -> Dict[str, str]:
        """
        Read all documents from a directory and return {filename: content}.
        """
        return read_all_texts(documents_dir)

    def assess_readiness(
        self,
        claim_type: str,
        documents_dir: str,
        claim_description: Optional[str] = None,
    ) -> Dict:
        """
        Assess document readiness for a claim.

        Args:
            claim_type: Type of claim (auto, home, health, life, travel).
            documents_dir: Directory containing the claim documents.
            claim_description: Optional description of the incident.

        Returns:
            Dict with readiness assessment.
        """
        file_list = list_claim_files(documents_dir)
        file_texts = self.inventory_documents(documents_dir)
        required = self.get_required_documents(claim_type)

        # Build a summary of available vs required
        present_names = list(file_texts.keys())
        missing = [d for d in required if not any(d.lower() in p.lower() for p in present_names)]

        # Use LLM for intelligent assessment
        available_summary = "\n".join([
            f"- {name}: {len(text)} chars" for name, text in file_texts.items()
        ])

        user_prompt = f"""Claim Type: {claim_type}
Claim Description: {claim_description or 'Not provided'}

Required documents for this claim type:
{chr(10).join('- ' + d for d in required)}

Available documents in folder:
{available_summary or 'No documents found'}

Files found: {', '.join(present_names) if present_names else 'None'}

Assess readiness."""

        assessment = self.llm.extract_json(
            system_prompt=DOCUMENT_CHECKER_SYSTEM,
            user_prompt=user_prompt,
        )

        assessment["claim_type"] = claim_type
        assessment["file_count"] = len(file_list)
        assessment["missing_basic"] = missing
        return assessment

    def generate_checklist(self, claim_type: str) -> str:
        """Generate a user-friendly document checklist."""
        required = self.get_required_documents(claim_type)
        lines = [
            f"📋 Document Checklist for {claim_type.title()} Claims",
            "",
            "Gather these documents before filing:",
        ]
        for i, doc in enumerate(required, 1):
            lines.append(f"  {i}. {doc}")

        lines.extend([
            "",
            "💡 Tip: Take photos of everything, even if the list doesn't mention it.",
            "📸 Photos with timestamps are gold for any claim.",
        ])
        return "\n".join(lines)