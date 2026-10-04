"""
Policy Parser Agent — Reads insurance policy documents (PDF/text) and extracts
key coverage terms, limits, deductibles, exclusions, and claim filing instructions
into structured data.
"""

from typing import Optional, Dict
from utils.llm_utils import LLMClient, get_llm_client
from utils.file_utils import extract_pdf_text, read_text_file


SYSTEM_PROMPT = """You are an insurance policy analyst. Given a policy document,
extract the following information as a JSON object:
{
  "policy_number": "string or null",
  "insurance_company": "string or null",
  "policy_type": "auto | home | health | life | travel | other",
  "coverage_start_date": "YYYY-MM-DD or null",
  "coverage_end_date": "YYYY-MM-DD or null",
  "premium_amount": "string or null",
  "deductible": "string or null",
  "coverage_limits": {"coverage_name": "limit_string"},
  "exclusions": ["list of key exclusions"],
  "claim_filing_instructions": "instructions or null",
  "key_terms_defined": [{"term": "...", "definition": "..."}]
}
Be thorough — read the ENTIRE document. If information is not present, use null.
Do NOT invent values."""


class PolicyParserAgent:
    """
    Agent 1: Parses an insurance policy and extracts structured coverage info.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()

    def parse_policy(self, filepath: str) -> Dict:
        """
        Parse an insurance policy PDF or text file.

        Args:
            filepath: Path to the policy document (.pdf or .txt).

        Returns:
            Dict with structured policy information.
        """
        text = None
        if filepath.lower().endswith(".pdf"):
            text = extract_pdf_text(filepath)
        else:
            try:
                text = read_text_file(filepath)
            except Exception:
                pass

        if not text or len(text.strip()) < 20:
            return {
                "error": "Could not extract meaningful text from policy document",
                "policy_number": None,
                "insurance_company": None,
            }

        # If document is very long, take first + last portions
        if len(text) > 12000:
            text = text[:6000] + "\n\n[...]\n\n" + text[-6000:]

        result = self.llm.extract_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"Extract insurance policy details from this document:\n\n{text}",
        )

        return result

    def summarize_in_plain_english(self, policy_data: Dict) -> str:
        """
        Convert the extracted policy data into a plain-English summary
        that a non-lawyer can understand.
        """
        user_prompt = f"""Turn this insurance policy data into a concise plain-English summary
for the policyholder. Use simple language. Highlight: what's covered, what's NOT covered,
how much they pay out of pocket (deductible), and how to file a claim.

Policy Data:
{policy_data}"""

        return self.llm.chat(
            system_prompt="You are a helpful insurance explainer. Translate insurance jargon into plain English. Be concise but thorough. Use bullet points.",
            user_prompt=user_prompt,
            temperature=0.3,
        )